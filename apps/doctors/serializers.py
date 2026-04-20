from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import serializers

from apps.user.models import User
from apps.specialties.models import Specialty
from apps.specialties.serializers import SpecialtySerializer

from .models import DoctorProfile


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

    @transaction.atomic
    def create(self, validated_data):
        specialties = validated_data.pop("specialties")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
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