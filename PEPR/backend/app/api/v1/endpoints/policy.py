from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.infrastructure.database import get_db
from app.models.policy import PolicyTarget, PolicyActual, PolicyGap
from app.schemas.policy import PolicyTargetResponse, PolicyTargetCreate, PolicyGapResponse, PolicyActualCreate
from app.services.analysis.policy_engine import PolicyEngine

router = APIRouter()

@router.get("/policy-targets", response_model=List[PolicyTargetResponse])
async def list_policy_targets(db: AsyncSession = Depends(get_db)):
    query = select(PolicyTarget)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/admin/policy-targets", response_model=PolicyTargetResponse)
async def create_policy_target(target: PolicyTargetCreate, db: AsyncSession = Depends(get_db)):
    db_target = PolicyTarget(**target.model_dump())
    db.add(db_target)
    await db.commit()
    await db.refresh(db_target)
    return db_target

@router.post("/admin/policy-actuals", response_model=PolicyGapResponse)
async def submit_actual_and_evaluate(actual: PolicyActualCreate, db: AsyncSession = Depends(get_db)):
    """
    Submits an actual value for a target, runs the engine, and creates a PolicyGap.
    """
    # Fetch target
    target_query = select(PolicyTarget).where(PolicyTarget.id == actual.target_id)
    result = await db.execute(target_query)
    db_target = result.scalars().first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
        
    # Create actual
    db_actual = PolicyActual(**actual.model_dump())
    db.add(db_actual)
    await db.commit()
    await db.refresh(db_actual)
    
    # Fetch history for persistence scoring
    history_query = select(PolicyGap).where(PolicyGap.target_id == db_target.id).order_by(PolicyGap.created_at.asc())
    history_result = await db.execute(history_query)
    historical_gaps = history_result.scalars().all()
    
    # Run Engine
    gap = PolicyEngine.calculate_gap(target=db_target, actual=db_actual, historical_gaps=historical_gaps)
    db.add(gap)
    await db.commit()
    await db.refresh(gap)
    
    return gap

from sqlalchemy.orm import joinedload

@router.get("/policy-gaps", response_model=List[PolicyGapResponse])
@router.get("/gaps", response_model=List[PolicyGapResponse])
@router.get("/policy/gaps", response_model=List[PolicyGapResponse])
@router.get("/policy/policy-gaps", response_model=List[PolicyGapResponse])
async def list_policy_gaps(db: AsyncSession = Depends(get_db)):
    # Use joinedload to return the full Gap Table (Target vs Actual) to the frontend
    query = select(PolicyGap).options(joinedload(PolicyGap.target), joinedload(PolicyGap.actual)).order_by(PolicyGap.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/policy-gaps/{id}", response_model=PolicyGapResponse)
async def get_policy_gap(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = select(PolicyGap).where(PolicyGap.id == id)
    result = await db.execute(query)
    gap = result.scalars().first()
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    return gap
