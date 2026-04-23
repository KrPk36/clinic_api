from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

from apps.common.models import GenderChoices

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User needs to provide an e-mail')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        su_user = self.create_user(email, password, **extra_fields)

        # Import here to avoid issues if the Group table doesn't exist yet
        try:
            from django.contrib.auth.models import Group
            admin_group, _ = Group.objects.get_or_create(name="Admin")
            su_user.groups.add(admin_group)
        except Exception:
            # If the auth tables aren't ready yet, skip silently.
            # The superuser can be added to the group manually afterwards.
            pass

        return su_user

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, unique=False, blank=False, null=False)
    last_name = models.CharField(max_length=50, unique=False, blank=False, null=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @property
    def username(self):
        return self.get_username()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class PatientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)

    def __str__(self):
        return f"{self.user.get_full_name()}"