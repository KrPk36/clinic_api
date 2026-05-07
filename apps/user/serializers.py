from django.contrib.auth.models import Group, Permission
from django.contrib.auth import authenticate
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from apps.doctors.serializers import DoctorReadSerializer

from .models import User, PatientProfile, GenderChoices

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError({'detail':'Invalid credentials'})
        
        data = super().validate(attrs)

        return data

class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")

class PatientReadSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(
        source="get_gender_display", read_only=True
    )

    class Meta:
        model = PatientProfile
        fields = [
            "date_of_birth",
            "gender",
            "phone",
        ]

class PatientCreateSerializer(serializers.Serializer):
    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    # Patient profile fields
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=GenderChoices.choices)
    phone = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        # specialties = validated_data.pop("specialties")

        # 1. Create the User
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )

        # 2. Assign to the Patient group
        patient_group = Group.objects.get(name="Patient")
        user.groups.add(patient_group)

        # 3. Create the linked PatientProfile
        profile = PatientProfile.objects.create(
            user=user,
            date_of_birth=validated_data["date_of_birth"],
            phone=validated_data["phone"],
            gender=validated_data["gender"],
        )

        return profile

class UserProfileReadSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "date_joined", "profile"]
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_profile(self, obj):
        if hasattr(obj, "patient_profile"):
            return PatientReadSerializer(obj.patient_profile).data
        if hasattr(obj, "doctor_profile"):
            return DoctorReadSerializer(obj.doctor_profile).data
        return None

class UserProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    phone = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()

        # Update phone on whichever profile exists
        phone = validated_data.get("phone")
        if phone:
            if hasattr(instance, "patient_profile"):
                instance.patient_profile.phone = phone
                instance.patient_profile.save(update_fields=["phone"])
            elif hasattr(instance, "doctor_profile"):
                instance.doctor_profile.phone = phone
                instance.doctor_profile.save(update_fields=["phone"])

        return instance