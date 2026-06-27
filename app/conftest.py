import pytest
import warnings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.service import Service
from app.models.schedule import Schedule
from app.models.booking import Booking, BookingStatus, PaymentStatus
from datetime import datetime, timedelta


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=Warning, module="sqlalchemy")
warnings.filterwarnings("ignore", category=Warning, module="pydantic")

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_customer(db):
    user = User(
        id=1,
        email="customer@test.com",
        username="testcustomer",
        full_name="Test Customer",
        hashed_password=get_password_hash("password123"),
        phone="1234567890",
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_provider(db):
    user = User(
        id=2,
        email="provider@test.com",
        username="testprovider",
        full_name="Test Provider",
        hashed_password=get_password_hash("password123"),
        phone="0987654321",
        role=UserRole.PROVIDER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_admin(db):
    user = User(
        id=3,
        email="admin@test.com",
        username="testadmin",
        full_name="Test Admin",
        hashed_password=get_password_hash("password123"),
        phone="5555555555",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_service(db, test_provider):
    service = Service(
        id=1,
        name="Test Service",
        description="This is a test service",
        category="Cleaning",
        price=100.00,
        duration_minutes=60,
        provider_id=test_provider.id,
        is_active=True
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@pytest.fixture
def test_schedule(db, test_service):
    start_time = datetime.now() + timedelta(days=1)
    schedule = Schedule(
        id=1,
        service_id=test_service.id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=test_service.duration_minutes),
        is_available=True
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@pytest.fixture
def test_booking(db, test_customer, test_provider, test_service, test_schedule):
    booking = Booking(
        id=1,
        customer_id=test_customer.id,
        provider_id=test_provider.id,
        service_id=test_service.id,
        schedule_id=test_schedule.id,
        status=BookingStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
        total_price=100.00,
        cancellation_deadline=datetime.now() + timedelta(hours=2)
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    test_schedule.is_available = False
    db.commit()
    
    return booking

@pytest.fixture
def customer_token(test_customer):
    """Create token directly using user ID"""
    return create_access_token(data={"sub": str(test_customer.id)})

@pytest.fixture
def provider_token(test_provider):
    return create_access_token(data={"sub": str(test_provider.id)})

@pytest.fixture
def admin_token(test_admin):
    return create_access_token(data={"sub": str(test_admin.id)})

@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}

@pytest.fixture
def provider_headers(provider_token):
    return {"Authorization": f"Bearer {provider_token}"}

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}