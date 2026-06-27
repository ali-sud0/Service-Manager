from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from pytest import Session

from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.seed import create_admin_user

from .core.database import engine, Base, get_db
from .routers.auth import router as auth_router
from .routers.users import router as users_router
from .routers.services import router as services_router
from .routers.bookings import router as bookings_router
from .routers.schedules import router as schedules_router
from .routers.payments import router as payments_router
from .routers.notifications import router as notifications_router
from .routers.dashboard import router as dashboard_router
from .routers.pdf import router as pdf_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    create_admin_user()
    yield


app = FastAPI(title="Service Booking System", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(services_router)
app.include_router(bookings_router)
app.include_router(schedules_router)
app.include_router(payments_router)
app.include_router(notifications_router)
app.include_router(dashboard_router)
app.include_router(pdf_router)


@app.get("/")
async def root(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
    ):
        """Redirect to dashboard if logged in, otherwise to login page"""
        if current_user:
            if current_user.role == "admin":
                return RedirectResponse(url="/dashboard/admin", status_code=302)
            elif current_user.role == "provider":
                return RedirectResponse(url="/dashboard/provider", status_code=302)
            else:
                return RedirectResponse(url="/services", status_code=302)
        else:
            return RedirectResponse(url="/auth/login", status_code=302)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}