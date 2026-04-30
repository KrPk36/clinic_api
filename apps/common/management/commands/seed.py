import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

from apps.user.models import User, PatientProfile
from apps.doctors.models import DoctorProfile, AvailabilitySchedule
from apps.specialties.models import Specialty
from apps.appointments.models import Appointment


# Seed data ---------------------------------------------------------------------------------------

SPECIALTIES = [
    {"name": "General Practice", "description": "Primary care and general health."},
    {"name": "Cardiology", "description": "Heart and cardiovascular system."},
    {"name": "Dermatology", "description": "Skin, hair and nail conditions."},
    {"name": "Pediatrics", "description": "Medical care for children and adolescents."},
    {"name": "Orthopedics", "description": "Musculoskeletal system and injuries."},
]

ADMIN = {
    "email": "admin@clinic.com",
    "first_name": "Richard",
    "last_name": "Anderson",
    "password": "Admin1234!",
}

DOCTORS = [
    {
        "email": "dr.smith@clinic.com",
        "first_name": "James",
        "last_name": "Smith",
        "password": "Doctor1234!",
        "bio": "15 years of experience in general practice.",
        "phone": "555-1001",
        "specialties": ["General Practice"],
    },
    {
        "email": "dr.johnson@clinic.com",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "password": "Doctor1234!",
        "bio": "Specialist in cardiovascular diseases.",
        "phone": "555-1002",
        "specialties": ["Cardiology"],
    },
    {
        "email": "dr.patel@clinic.com",
        "first_name": "Anil",
        "last_name": "Patel",
        "password": "Doctor1234!",
        "bio": "Experienced dermatologist and skin surgeon.",
        "phone": "555-1003",
        "specialties": ["Dermatology", "General Practice"],
    },
]

PATIENTS = [
    {
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Turner",
        "password": "Patient1234!",
        "date_of_birth": "1990-04-15",
        "phone": "555-2001",
        "gender": "F",
    },
    {
        "email": "bob@example.com",
        "first_name": "Bob",
        "last_name": "Martin",
        "password": "Patient1234!",
        "date_of_birth": "1985-08-22",
        "phone": "555-2002",
        "gender": "M",
    },
    {
        "email": "carol@example.com",
        "first_name": "Carol",
        "last_name": "White",
        "password": "Patient1234!",
        "date_of_birth": "2000-01-10",
        "phone": "555-2003",
        "gender": "F",
    },
]

# day_of_week: 0=Mon, 1=Tue ... 4=Fri
SCHEDULES = [
    {"day_of_week": 0, "start_time": "08:00", "end_time": "13:00"},
    {"day_of_week": 1, "start_time": "08:00", "end_time": "13:00"},
    {"day_of_week": 2, "start_time": "10:00", "end_time": "15:00"},
    {"day_of_week": 3, "start_time": "08:00", "end_time": "13:00"},
    {"day_of_week": 4, "start_time": "09:00", "end_time": "14:00"},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_or_create_group(name):
    group, _ = Group.objects.get_or_create(name=name)
    return group


def next_weekday(weekday):
    """Returns the next future date matching the given weekday (0=Mon)."""
    today = datetime.date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


# ── Command ────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seeds the database with demo data for development and portfolio purposes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Clear all existing seed data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing data...")
            Appointment.objects.all().delete()
            AvailabilitySchedule.objects.all().delete()
            DoctorProfile.objects.all().delete()
            PatientProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Specialty.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing data cleared."))

        self.stdout.write("Seeding groups...")
        admin_group = get_or_create_group("Admin")
        doctor_group = get_or_create_group("Doctor")
        patient_group = get_or_create_group("Patient")

        self.stdout.write("Creating admin(superuser)...")
        if User.objects.filter(email=ADMIN["email"]).exists():
            self.stdout.write(f"  Admin '{ADMIN['email']}' already exists, skipping.")
        else:
            admin = User.objects.create_superuser(
                email=ADMIN["email"], 
                password=ADMIN["password"],
                first_name=ADMIN["first_name"],
                last_name=ADMIN["last_name"],
            )
            admin.groups.add(admin_group)
            self.stdout.write(f"  Admin '{admin.get_full_name()}' created.")


        self.stdout.write("Seeding specialties...")
        specialty_map = {}
        for data in SPECIALTIES:
            specialty, created = Specialty.objects.get_or_create(
                name=data["name"],
                defaults={"description": data["description"]},
            )
            specialty_map[specialty.name] = specialty
            label = "created" if created else "already exists"
            self.stdout.write(f"  Specialty '{specialty.name}' {label}.")

        self.stdout.write("Seeding doctors...")
        doctor_profiles = []
        for data in DOCTORS:
            if User.objects.filter(email=data["email"]).exists():
                self.stdout.write(f"  Doctor '{data['email']}' already exists, skipping.")
                doctor_profiles.append(
                    DoctorProfile.objects.get(user__email=data["email"])
                )
                continue

            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            user.groups.add(doctor_group)

            profile = DoctorProfile.objects.create(
                user=user,
                bio=data["bio"],
                phone=data["phone"],
            )
            profile.specialties.set(
                [specialty_map[s] for s in data["specialties"]]
            )
            doctor_profiles.append(profile)
            self.stdout.write(f"  Doctor '{user.get_full_name()}' created.")

        self.stdout.write("Seeding schedules...")
        for profile in doctor_profiles:
            for sched in SCHEDULES:
                AvailabilitySchedule.objects.get_or_create(
                    doctor=profile,
                    day_of_week=sched["day_of_week"],
                    defaults={
                        "start_time": sched["start_time"],
                        "end_time": sched["end_time"],
                    },
                )
            self.stdout.write(f"  Schedules set for Dr. {profile.user.get_full_name()}.")

        self.stdout.write("Seeding patients...")
        patient_profiles = []
        for data in PATIENTS:
            if User.objects.filter(email=data["email"]).exists():
                self.stdout.write(f"  Patient '{data['email']}' already exists, skipping.")
                patient_profiles.append(
                    PatientProfile.objects.get(user__email=data["email"])
                )
                continue

            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            user.groups.add(patient_group)

            profile = PatientProfile.objects.create(
                user=user,
                date_of_birth=data["date_of_birth"],
                phone=data["phone"],
                gender=data["gender"],
            )
            patient_profiles.append(profile)
            self.stdout.write(f"  Patient '{user.get_full_name()}' created.")

        self.stdout.write("Seeding appointments...")
        # Book one future appointment per patient with a random doctor
        for patient in patient_profiles:
            doctor = random.choice(doctor_profiles)
            # Pick a schedule block and find its next occurrence
            schedule = AvailabilitySchedule.objects.filter(doctor=doctor).first()
            appointment_date = next_weekday(schedule.day_of_week)

            already_exists = Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                start_time=schedule.start_time,
            ).exists()

            if already_exists:
                self.stdout.write(
                    f"  Appointment slot for '{patient.user.get_full_name()}' already exists, skipping."
                )
                continue

            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=appointment_date,
                start_time=schedule.start_time,
                end_time=datetime.datetime.combine(
                    datetime.date.today(),
                    schedule.start_time
                ) + datetime.timedelta(minutes=30),
                status=Appointment.Status.SCHEDULED,
            )
            self.stdout.write(
                f"  Appointment booked for '{patient.user.get_full_name()}' "
                f"with Dr. {doctor.user.get_full_name()} on {appointment_date}."
            )

        self.stdout.write(self.style.SUCCESS("\nDatabase seeded successfully."))
        self.stdout.write("\nDemo credentials:")
        self.stdout.write("  Admin    - password: Admin1234!")
        self.stdout.write("    admin@clinic.com")
        self.stdout.write("  Doctors  - password: Doctor1234!")
        self.stdout.write("    dr.smith@clinic.com")
        self.stdout.write("    dr.johnson@clinic.com")
        self.stdout.write("    dr.patel@clinic.com")
        self.stdout.write("  Patients - password: Patient1234!")
        self.stdout.write("    alice@example.com")
        self.stdout.write("    bob@example.com")
        self.stdout.write("    carol@example.com")