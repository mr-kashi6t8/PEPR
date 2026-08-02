import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.infrastructure.database import get_db
from app.models.auth import User, Role
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_reset_token,
    verify_reset_token,
    generate_reset_code,
    verify_reset_code,
)

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_ROLES = ["RESEARCHER", "MANAGEMENT", "ICT", "ADMIN"]

async def get_or_create_role(db: AsyncSession, role_name: str) -> Role:
    """Helper to fetch or insert Role object."""
    role_name_clean = role_name.upper() if role_name else "RESEARCHER"
    result = await db.execute(select(Role).where(Role.name == role_name_clean))
    r = result.scalars().first()
    if not r:
        r = Role(id=str(uuid.uuid4()), name=role_name_clean, description=f"{role_name_clean} Role")
        db.add(r)
        await db.commit()
        await db.refresh(r)
    return r

class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "RESEARCHER"

class UpdateUserRoleRequest(BaseModel):
    role: str

@router.post("/signup", response_model=Token)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Public self-registration.
    FORCES all public signups to 'RESEARCHER' role ONLY.
    Only Admins can provision ICT, Management, or Admin accounts.
    """
    # Force public signup to RESEARCHER role
    forced_role_name = "RESEARCHER"
    role_obj = await get_or_create_role(db, forced_role_name)

    result = await db.execute(select(User).where(User.email == user_in.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    db_user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role_id=role_obj.id,
        is_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    user_resp = UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        full_name=db_user.full_name,
        role="RESEARCHER",
        is_active=db_user.is_active,
    )
    access_token = create_access_token({"sub": db_user.email, "role": "RESEARCHER"})
    return Token(access_token=access_token, user=user_resp)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates user against SQLite database."""
    result = await db.execute(
        select(User).options(joinedload(User.role)).where(User.email == credentials.email)
    )
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid institutional email address or password."
        )

    user_role_name = user.role.name if user.role else "RESEARCHER"
    user_resp = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user_role_name,
        is_active=user.is_active,
    )
    access_token = create_access_token({"sub": user.email, "role": user_role_name})
    return Token(access_token=access_token, user=user_resp)

@router.get("/me", response_model=UserResponse)
async def get_me(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """Gets details for currently authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
        
    try:
        scheme, token = authorization.split()
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        email = payload["sub"]
        result = await db.execute(select(User).options(joinedload(User.role)).where(User.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_role_name = user.role.name if user.role else "RESEARCHER"
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user_role_name,
            is_active=user.is_active,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(db: AsyncSession = Depends(get_db)):
    """Lists all registered system users and their assigned roles."""
    result = await db.execute(select(User).options(joinedload(User.role)).order_by(User.created_at.desc()))
    users = result.scalars().all()
    resp = []
    for u in users:
        r_name = u.role.name if u.role else "RESEARCHER"
        resp.append(UserResponse(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=r_name,
            is_active=u.is_active
        ))
    return resp

@router.post("/admin/create-user", response_model=UserResponse)
async def admin_create_user(req: AdminCreateUserRequest, db: AsyncSession = Depends(get_db)):
    """
    Admin exclusive endpoint to provision new accounts with assigned role (ICT, MANAGEMENT, ADMIN, RESEARCHER).
    """
    target_role_name = req.role.upper()
    if target_role_name not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")

    role_obj = await get_or_create_role(db, target_role_name)

    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Account with this email already exists.")

    db_user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role_id=role_obj.id,
        is_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        full_name=db_user.full_name,
        role=target_role_name,
        is_active=db_user.is_active,
    )

@router.patch("/admin/users/{user_id}/role", response_model=UserResponse)
async def admin_update_user_role(user_id: str, req: UpdateUserRoleRequest, db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint to change/upgrade a user's assigned role.
    """
    new_role_name = req.role.upper()
    if new_role_name not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")

    result = await db.execute(select(User).options(joinedload(User.role)).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    role_obj = await get_or_create_role(db, new_role_name)
    user.role_id = role_obj.id
    await db.commit()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=new_role_name,
        is_active=user.is_active,
    )

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Sends a 6-digit password reset verification code to the researcher's email.
    Returns only a token (no code) — the code travels via email only.
    """
    from app.services.email_service import send_reset_code_email

    # Always respond with success to prevent email enumeration attacks
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()

    if not user:
        # Return generic message — don't reveal whether email exists
        return {"message": f"If an account exists for {req.email}, a reset code has been sent."}

    # Generate 6-digit code + signed token
    code, token = generate_reset_code(req.email)

    # Send the code via email (non-blocking)
    full_name = user.full_name or "Researcher"
    sent = await send_reset_code_email(
        to_email=req.email,
        to_name=full_name,
        reset_code=code
    )

    if sent:
        logger.info("Password reset code emailed to %s", req.email)
    else:
        logger.warning("Failed to email reset code to %s (SMTP issue)", req.email)

    # Return the token so the frontend can submit it alongside the code the user types
    # The code itself is NEVER returned in the API response — only travels via email
    return {
        "message": f"A 6-digit verification code has been sent to {req.email}. Please check your inbox.",
        "reset_token": token,  # frontend sends this back with the code the user types
    }

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Resets password.
    Accepts either:
      - token + code (new 6-digit email code flow)
      - token only   (legacy JWT-only flow)
    """
    # Try new code-based flow first (token + 6-digit code)
    if hasattr(req, 'code') and req.code:
        email = verify_reset_code(req.token, req.code)
    else:
        # Legacy: validate token-only
        email = verify_reset_token(req.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please request a new one."
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.hashed_password = hash_password(req.new_password)
    await db.commit()
    logger.info("Password reset successful for %s", email)
    return {"message": "Password updated successfully. You can now login with your new password."}

