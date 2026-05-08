# Clinic Management API

A RESTful API for a fictional medical clinic, built as a portfolio project to demonstrate proficiency in backend development with Python and Django REST Framework.

The system supports the full lifecycle of clinic operations: patient self-registration, doctor and specialty management, weekly availability scheduling, appointment booking, and role-based access control. All documented through an auto-generated Swagger UI.

![CI](https://github.com/KrPk36/clinic_api/actions/workflows/ci.yml/badge.svg)
---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Roles & Permissions](#roles--permissions)
- [Getting Started](#getting-started)
- [Seeding the Database](#seeding-the-database)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Known Limitations & Future Work](#known-limitations--future-work)

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.13+ |
| Framework | Django 6 + Django REST Framework |
| Database | PostgreSQL 16 |
| Auth | djangorestframework-simplejwt |
| API Docs | drf-spectacular (OpenAPI 3.0 / Swagger UI) |
| Containerization | Docker + Docker Compose |

---

## Architecture Overview

The project follows a strict separation between serializers and views:

- **Models** define schema and relationships only, no business logic.
- **Serializers** handle validation and object creation/mutation, always returning model instances.
- **Views** own the HTTP layer. They call serializers, build responses, and handle status codes.

Authentication is handled via JWT. Every protected endpoint requires an `Authorization: Bearer <access_token>` header. Roles are implemented using Django's built-in `Group` system, each user belongs to exactly one group (`Admin`, `Doctor`, or `Patient`).

### Data Model

```
User (custom, email-based)
 ├── PatientProfile (1-to-1)   date_of_birth, phone, gender
 └── DoctorProfile  (1-to-1)   bio, phone, is_active
      ├── Specialty (M-to-M)   name, description
      ├── AvailabilitySchedule  day_of_week, start_time, end_time, effective_until
      └── Appointment           date, start_time, end_time, status, notes
```

---

## Roles & Permissions

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access to all endpoints. Manages doctors, specialties, and all appointments. |
| **Doctor** | Manages own availability schedule. Views and completes own appointments. |
| **Patient** | Self-registers. Books and cancels own appointments. Views own appointment history. |

> Admins are created manually via the Django admin panel or the `createsuperuser` management command. Patients self-register via `POST /api/auth/register/`. Doctors are registered by an admin via `POST /api/doctors/`.

---

## Getting Started

### Prerequisites

- Docker & Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/KrPk36/clinic_api.git
cd clinic_api
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your values

### 3. Start the containers

```bash
docker compose up --build
```

This starts two services: the Django API on `http://localhost:8000` and a PostgreSQL database.

### 4. Migrations

The entrypoint script automatically runs migrations on start.

### 5. Create an admin user

You can manually create an admin user to test the project:

```bash
docker compose exec web python manage.py createsuperuser
```

This step is optional if you decide to use the `seed` command explained ahead.

### 6. Access the API documentation

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| OpenAPI Schema | http://localhost:8000/schema/ |

---

## Seeding the Database

A management command is provided to populate the database with demo data so the API can be explored immediately without manual setup.

```bash
# Seed demo data
docker compose exec api python manage.py seed

# Wipe all data and reseed from scratch
docker compose exec api python manage.py seed --flush
```

### Demo credentials

After seeding, the following accounts are available:

**Admin** - password `Admin1234!`
| Name | Email |
|------|-------|
| Richard Anderson | admin@clinic.com |

**Doctors** - password: `Doctor1234!`
| Name | Email |
|------|-------|
| James Smith | dr.smith@clinic.com |
| Sarah Johnson | dr.johnson@clinic.com |
| Anil Patel | dr.patel@clinic.com |

**Patients** - password: `Patient1234!`
| Name | Email |
|------|-------|
| Alice Turner | alice@example.com |
| Bob Martin | bob@example.com |
| Carol White | carol@example.com |

---

## API Reference

Full interactive documentation is available at `/api/docs/`. Below is a summary of all endpoints.

### Auth — `/auth/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/register/` | Public | Patient self-registration |
| `POST` | `/login/` | Public | Obtain JWT access + refresh tokens. |
| `POST` | `/token/refresh/` | Public | Refresh access token. |
| `GET` | `/me/` | Any auth | View own profile |
| `PATCH` | `/me/` | Any auth | Update own profile (name, phone, password) |

### Specialties — `/api/specialties/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET` | `/specialties/` | Public | List all specialties |
| `POST` | `/specialties/` | Admin | Create a specialty |
| `GET` | `/specialties/{id}/` | Public | Retrieve a specialty |
| `PATCH` | `/specialties/{id}/` | Admin | Update a specialty |
| `DELETE` | `/specialties/{id}/` | Admin | Delete a specialty |

### Doctors — `/api/doctors/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET` | `/doctors/` | Public | List active doctors. Supports `?specialty_id=` filter |
| `POST` | `/doctors/` | Admin | Register a new doctor |
| `GET` | `/doctors/{id}/` | Public | Retrieve a doctor's profile |
| `PATCH` | `/doctors/{id}/` | Admin | Update a doctor's profile |
| `DELETE` | `/doctors/{id}/` | Admin | Soft-deactivate a doctor |

### Availability Schedules — `/api/doctors/{id}/schedules/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET` | `/schedules/` | Public | List a doctor's schedule blocks |
| `POST` | `/schedules/` | Admin / Doctor (own) | Add a weekly availability block |
| `GET` | `/schedules/{id}/` | Public | Retrieve a schedule block |
| `PATCH` | `/schedules/{id}/` | Admin / Doctor (own) | Update a schedule block |
| `DELETE` | `/schedules/{id}/` | Admin / Doctor (own) | Hard delete (only if no future appointments) |
| `PATCH` | `/schedules/{id}/deactivate/` | Admin / Doctor (own) | Soft-expire a block via `effective_until` date |

### Appointments — `/api/appointments/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET` | `/appointments/` | Patient / Doctor | List own appointments. Supports `?status=` filter |
| `POST` | `/appointments/` | Patient | Book an appointment |
| `GET` | `/appointments/{id}/` | Patient / Doctor (own) | Retrieve an appointment |
| `PATCH` | `/appointments/{id}/cancel/` | Patient (own) | Cancel a scheduled appointment |
| `PATCH` | `/appointments/{id}/complete/` | Doctor (own) / Admin | Mark an appointment as completed |

### Health — `/api/health/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET` | `/health/` | Public | Service and database health check |

---

## Project Structure

```
clinic_api/
├── clinic_api/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── common/              # Shared permissions, throttling, health check
│   │   └── management/
│   │       └── commands/
│   │           └── seed.py  # Demo data seeder
│   ├── user/                # Custom user model, auth endpoints, patient profile
│   ├── specialties/         # Specialty model and views
│   ├── doctors/             # DoctorProfile, schedules, available slots
│   └── appointments/        # Appointment model and views
├── compose.yaml
├── Dockerfile
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Design Decisions

**Soft deletes over hard deletes**: Doctors are never removed from the database; they are deactivated via an `is_active` flag. This preserves the integrity of historical appointment records. The same principle applies to availability schedule blocks, which can be soft-expired via an `effective_until` date rather than deleted outright when future appointments exist.

**Slot boundary enforcement**: Appointments are restricted to start on the hour or half hour (`:00` or `:30`). This is a business rule, not just a UX convenience — it makes overlap detection trivial (exact `start_time` match) and reflects how real clinics operate.

**Fixed slot duration**: All appointments have a fixed duration of 30 minutes, derived server-side from the booking start time. Clients never submit an `end_time`, preventing arbitrary time blocks.

**Group-based RBAC without third-party packages**: Role-based access control is implemented entirely using Django's built-in `Group` system. Role assignment happens at registration time and is enforced through custom DRF permission classes.

---

## Known Limitations

These are intentional scope exclusions for this portfolio project, noted here to demonstrate domain awareness:

- **Room management**: A real clinic has a finite number of consultation rooms. A `Room` model with a `unique_together` constraint on `(room, date, start_time)` would prevent double-booking of physical spaces.
- **Email notifications**: Appointment confirmations, reminders, and cancellation notices would be handled via a task queue (e.g. Celery + Redis) in a production system.
- **Schedule transition periods**: The `effective_until` field on `AvailabilitySchedule` supports graceful schedule changes, but notifying affected patients and reassigning appointments would require additional tooling.
- **Patient medical records**: A production clinic system would require a separate, access-controlled records module.
- **Recurring appointments**: Currently each appointment is a standalone booking. Recurring series would require a separate model and more complex conflict detection.
- **Payment processing**: No billing or invoice generation is implemented.
- **Multi-language support**: The API responses are English-only.
