# RealSuccess Event Companion & Admin Backend API

Production-ready backend built with **Django 5.1**, **Django REST Framework (DRF)**, **PostgreSQL 15**, **Redis 7**, **Celery 5**, **Channels**, and **drf-spectacular**.

Architected specifically to power both the **RealSuccess Mobile Application** and the **RealSuccess Admin Management Dashboard**.

---

## 🌐 Production & Public Compliance Links

| Resource | URL | Description |
|---|---|---|
| **Live Production API** | `https://api.ourrealsuccess.com/` | Primary API Gateway |
| **Interactive Swagger UI** | `https://api.ourrealsuccess.com/api/docs/` | Complete OpenAPI 3.0 documentation |
| **ReDoc Schema** | `https://api.ourrealsuccess.com/api/redoc/` | Public API specification reference |
| **OpenAPI Schema (JSON)** | `https://api.ourrealsuccess.com/api/schema/` | Raw OpenAPI Schema JSON |
| **Live Admin Dashboard** | `https://admin.ourrealsuccess.com/` | Web Admin Management Portal |
| **Privacy Policy (Public URL)** | `https://api.ourrealsuccess.com/privacy/` | App Store & Google Play compliance URL |
| **Terms & Conditions (Public URL)** | `https://api.ourrealsuccess.com/terms/` | App Store & Google Play compliance URL |

---

## 📱 Mobile App Key Endpoints for Frontend Developers

### 1. Social Authentication (Google / Apple Login)
- **Endpoint**: `POST /api/auth/social-auth/` *(also aliases `/api/auth/social-login/`)*
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "provider": "google"
  }
  ```
  *(Note: `first_name`, `last_name`, and `provider` are optional; defaults to `"google"`)*
- **Response**:
  ```json
  {
    "success": true,
    "message": "Login successful",
    "status_code": 200,
    "data": {
      "access": "eyJhbGciOiJIUzI1NiIsIn...",
      "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
      "user": {
        "id": 10,
        "email": "user@example.com",
        "name": "John Doe",
        "social_auth_provider": "google"
      }
    }
  }
  ```

### 2. User Data & Account Deletion API
Permanently purges the user record, profile, ticket purchases, chat messages, and authentication tokens.
- **Endpoint**: `POST /api/auth/delete-user-data/` *(also aliases `/api/auth/user/delete/`)*
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
  *(Or call with `Authorization: Bearer <token>` without payload to delete the authenticated user)*
- **Response**:
  ```json
  {
    "success": true,
    "message": "All data and account for user@example.com have been permanently deleted successfully.",
    "status_code": 200,
    "data": {
      "email": "user@example.com",
      "deleted": true
    }
  }
  ```

### 3. Dedicated Privacy Policy API
- **Endpoint**: `GET /api/content/privacy/`
- **Auth**: Public
- **Response**:
  ```json
  {
    "success": true,
    "message": "Privacy policy retrieved successfully",
    "status_code": 200,
    "data": {
      "title": "Privacy Policy",
      "content": "<h1>Real Success Privacy Policy</h1><p>...</p>",
      "updated_at": "2026-11-24T04:21:31.297876Z"
    }
  }
  ```

### 4. Dedicated Terms & Conditions API
- **Endpoint**: `GET /api/content/terms/`
- **Auth**: Public
- **Response**:
  ```json
  {
    "success": true,
    "message": "Terms and conditions retrieved successfully",
    "status_code": 200,
    "data": {
      "title": "Terms & Conditions",
      "content": "<h1>Real Success Terms & Conditions</h1><p>...</p>",
      "updated_at": "2026-11-24T04:21:31.297876Z"
    }
  }
  ```

---

## 🚀 Quick Start with Docker

```bash
# Clone the repository
git clone git@github.com:asyncrafi/realsuccess-backend.git
cd realsuccess-backend

# Configure environment variables
cp .env.example .env

# Start all containerized services
docker compose -f docker-compose.yml up -d --build

# Run migrations
docker compose exec backend python manage.py migrate

# Seed realistic database records (matching Figma designs)
docker compose exec backend python scripts/seed_data.py

# Check status
docker compose ps
```

---

## 📱 Mobile App Screens & Backend API Mapping

| Figma Screen | Node ID | Endpoint | Description |
|---|---|---|---|
| **Access Code** | `2363:694` | `POST /api/events/verify-access-code/` | Verifies event access code (e.g. `RS-AUG-2026-001`) before granting event access |
| **Welcome Back (Login/OTP)** | `2363:695` | `POST /api/auth/login/`<br>`POST /api/auth/otp/request/`<br>`POST /api/auth/otp/verify/` | JWT login or passwordless OTP login via email/phone |
| **Social Login** | `2363:695` | `POST /api/auth/social-auth/` | Direct Google/Apple social authentication |
| **Home Page** | `2363:696` | `GET /api/events/current/`<br>`GET /api/announcements/latest/`<br>`GET /api/resources/featured/` | Active event card, live countdown, announcements, quick cards |
| **Event Schedule** | `2363:697` | `GET /api/schedule/sessions/?day={1,2,3}&type={keynote,workshop}`<br>`GET /api/schedule/speakers/` | Day tabs, track filters, timeline cards, keynote speakers |
| **Session Details** | `2363:698` | `GET /api/schedule/sessions/{id}/`<br>`POST /api/schedule/sessions/{id}/bookmark/` | Venue, speaker card, downloadable session materials |
| **Speaker Profile** | `2363:699` | `GET /api/schedule/speakers/{id}/` | Avatar, bio, areas of expertise tags, speaker's sessions |
| **My Ticket** | `2363:700` | `GET /api/tickets/my-ticket/`<br>`POST /api/tickets/{id}/check-in/` | Attendee QR badge, ticket ID, VIP tier, check-in status |
| **Message Team / Concierge** | `2363:701` | `GET /api/chat/team/`<br>`POST /api/chat/messages/` | Concierge chat, direct coordinator messages |
| **Resources** | `2363:702` | `GET /api/resources/?category={Guides,PDF,Doc}`<br>`POST /api/resources/{id}/download/` | Featured resource, download counter, categorized guides |
| **Announcements** | `2363:703` | `GET /api/announcements/`<br>`GET /api/announcements/{id}/` | Priority banners, takeaway time/venue, attachments |
| **Profile & Settings** | `2363:704` | `GET /api/auth/profile/`<br>`POST /api/auth/change-password/`<br>`POST /api/auth/delete-user-data/`<br>`GET /api/content/privacy/`<br>`GET /api/content/terms/` | Attendee profile, password change, account deletion, legal content |

---

## 💻 Admin Dashboard Views & Backend API Mapping

| Dashboard Feature | Frontend Route | Backend Endpoint | Method |
|---|---|---|---|
| **Overview Dashboard** | `/dashboard` | `/api/reports/dashboard-stats/`<br>`/api/reports/attendance-overview/` | `GET` |
| **Events Management** | `/events` | `/api/events/`<br>`/api/events/{id}/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Schedule & Sessions** | `/schedule` | `/api/schedule/sessions/`<br>`/api/schedule/sessions/{id}/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Speakers Directory** | `/schedule` | `/api/schedule/speakers/`<br>`/api/schedule/speakers/{id}/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Tickets Management** | `/tickets` | `/api/tickets/`<br>`/api/tickets/{id}/check-in/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Attendees Roster** | `/attendees` | `/api/tickets/attendees/`<br>`/api/tickets/attendees/{id}/` | `GET`, `PUT`, `DELETE` |
| **Announcements** | `/announcements` | `/api/announcements/`<br>`/api/announcements/{id}/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Resources & Downloads**| `/resources` | `/api/resources/`<br>`/api/resources/{id}/` | `GET`, `POST`, `PUT`, `DELETE` |
| **Message Team (Staff)** | `/message-team` | `/api/team/team/`<br>`/api/team/messages/` | `GET`, `POST` |
| **Analytics & Reports** | `/reports` | `/api/reports/summary/`<br>`/api/reports/attendance-overview/`<br>`/api/reports/monthly-growth/` | `GET` |
| **Settings & Legal** | `/settings` | `/api/content/legal/`<br>`/api/content/faq/`<br>`/api/auth/profile/`<br>`/api/auth/password/change/` | `GET`, `PUT`, `POST` |

---

## 🔑 Default Superuser Credentials

- **Email**: `admin@ourrealsuccess.com`
- **Password**: `Admin@RealSuccess2026!`
- **Role**: Superuser / Platform Administrator

---

## 📦 Architecture & Standards

1. **Modular Django Structure**: Apps separated by domain (`accounts`, `core`, `events`, `schedule`, `tickets`, `announcements`, `resources`, `message_team`, `reports`, `content_settings`).
2. **Unified Response Format**: All endpoints return standard format with `success`, `message`, `status_code`, and `data`.
3. **JWT Authentication**: Short-lived Access Tokens with secure refresh token rotation via SimpleJWT.
4. **Spectacular OpenAPI 3.0**: Fully documented and browsable via Swagger UI at `/api/docs/`.
