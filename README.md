# Service Booking System

A complete online service management and booking system built with FastAPI and Tailwind CSS

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.x-06B6D4.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## About The Project

**Service Booking System** is a comprehensive platform for managing and booking online services, serving three main user roles:

- **Admin**: Complete system management (users, services, bookings, reports)
- **Service Provider**: Register and manage services, schedules, and bookings
- **Customer**: Search, book, pay, and manage service reservations

### Key Features

- Secure JWT authentication with role-based access control
- Three user roles with different permissions (Admin, Provider, Customer)
- Complete service management (Create, Read, Update, Delete)
- Advanced booking system with conflict prevention
- Online payment simulation with transaction tracking
- Real-time notifications using WebSocket
- Dedicated dashboards with interactive statistical charts
- Advanced service search and filtering (name, category, price, provider)
- PDF report generation (invoices, customer reports, provider reports, admin stats)
- Responsive and modern UI with Tailwind CSS
- Comprehensive unit tests (60+ tests passing)

---

## Technologies Used

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.104.1 | Main web framework |
| SQLAlchemy | 2.0.23 | ORM and database management |
| SQLite | - | Internal database |
| JWT | python-jose 3.3.0 | Authentication |
| WebSocket | websockets 12.0 | Real-time notifications |
| ReportLab | 4.0.4 | PDF generation |
| Pillow | 10.1.0 | Image processing |
| Passlib | 1.7.4 | Password hashing |
| Python-Multipart | 0.0.6 | Form data processing |

### Frontend

| Technology | Purpose |
|------------|---------|
| Tailwind CSS | Styling and responsive design |
| Chart.js | Statistical charts and graphs |
| Font Awesome | Icons and visual elements |
| Vanilla JS | Client-side interactions and API calls |

### Testing

| Technology | Purpose |
|------------|---------|
| Pytest | Testing framework |
| Pytest-Asyncio | Async function testing |
| HTTPX | HTTP client for testing |


---

## Installation & Setup

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)

### Installation Steps
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
uvicorn app.main:app --reload --port 8000
