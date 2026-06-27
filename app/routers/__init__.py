from .auth import router as auth_router
from .users import router as users_router
from .services import router as services_router
from .bookings import router as bookings_router
from .schedules import router as schedules_router
from .payments import router as payments_router
from .notifications import router as notifications_router
from .dashboard import router as dashboard_router
from .pdf import router as pdf_router

__all__ = [
    'auth_router',
    'users_router', 
    'services_router',
    'bookings_router',
    'schedules_router',
    'payments_router',
    'notifications_router',
    'dashboard_router',
    'pdf_router'
]