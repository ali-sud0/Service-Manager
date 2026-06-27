from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole

def create_admin_user():
    """Create admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if not admin:
            # Create admin user
            hashed_password = get_password_hash("admin123")
            admin_user = User(
                email="admin@servicehub.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=hashed_password,
                phone="09123456789",
                role=UserRole.ADMIN.value,
                is_active=True,
                profile_image="default.jpg"
            )
            db.add(admin_user)
            db.commit()
            
    except Exception as e:
        print(e)
        db.rollback()
    finally:
        db.close()