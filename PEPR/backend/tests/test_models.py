from datetime import datetime
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate
from app.schemas.economy import EconomicIndicatorCreate
from app.models.economy import EconomicIndicator
from app.models.auth import User

def test_user_schema_validation():
    # Valid user
    user = UserCreate(email="test@example.com", password="pwd", role_id=str(uuid4()))
    assert user.email == "test@example.com"
    
    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="pwd", role_id=str(uuid4()))

def test_indicator_schema_validation():
    indicator = EconomicIndicatorCreate(name="GDP", code="GDP_01")
    assert indicator.name == "GDP"
    assert indicator.code == "GDP_01"

def test_sqlalchemy_model_instantiation():
    user_id = uuid4()
    db_user = User(id=user_id, email="test@example.com", hashed_password="pwd")
    assert db_user.email == "test@example.com"
    assert db_user.id == user_id
    
    indicator = EconomicIndicator(name="CPI", code="CPI_01")
    assert indicator.name == "CPI"
