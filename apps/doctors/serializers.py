from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from datetime import date
from apps.user.models import User
from apps.specialties.models import Specialty
from apps.specialties.serializers import SpecialtySerializer

from .models import DoctorProfile, AvailabilitySchedule


class DoctorReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "name", "bio", "phone", "specialties"]

class DoctorSerializer(serializers.Serializer):
    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    # Doctor profile fields
    bio = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField()
    specialty_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        many=True,
        source="specialties"
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        specialties = validated_data.pop("specialties")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            is_staff=True,
        )

        doctor_group = Group.objects.get(name="Doctor")
        user.groups.add(doctor_group)

        profile = DoctorProfile.objects.create(
            user=user,
            bio=validated_data.get("bio", ""),
            phone=validated_data["phone"],
        )
        profile.specialties.set(specialties)
        return profile
    
    @transaction.atomic
    def update(self, instance, validated_data):
        specialties = validated_data.pop("specialties", None)

        user = instance.user
        user.email = validated_data.get("email", user.email)
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        if "password" in validated_data:
            user.set_password(validated_data["password"])
        user.save()

        instance.bio = validated_data.get("bio", instance.bio)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.save()

        # Update specialties only if provided
        if specialties is not None:
            instance.specialties.set(specialties)
        return instance

class AvailabilityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySchedule
        fields = ["id", "day_of_week", "start_time", "end_time", "effective_until"]

    def validate(self, data):
        doctor = self.context.get("doctor")
        day = data.get("day_of_week", getattr(self.instance, "day_of_week", None))
        start = data.get("start_time", getattr(self.instance, "start_time", None))
        end = data.get("end_time", getattr(self.instance, "end_time", None))
        effective_until = data.get("effective_until", getattr(self.instance, "effective_until", None))

        # end_time must be after start_time
        if start and end and end <= start:
            raise serializers.ValidationError("end_time must be after start_time.")

        # Check for overlapping blocks on the same doctor and day
        overlapping = AvailabilitySchedule.objects.filter(
            doctor=doctor,
            day_of_week=day,
            start_time__lt=end,
            end_time__gt=start,
        ).filter(
            Q(effective_until__isnull=True)|Q(effective_until__gte=date.today())
        )
        
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)

        if overlapping.exists():
            raise serializers.ValidationError(
                "This schedule block overlaps with an existing one."
            )

        return data
