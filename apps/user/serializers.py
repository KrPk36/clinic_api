from django.contrib.auth.models import Group, Permission
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

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
    date_of_birth = serializers.DateField(
        source="patient_profile.date_of_birth", read_only=True
    )
    gender = serializers.CharField(
        source="patient_profile.get_gender_display", read_only=True
    )
    phone = serializers.CharField(
        source="patient_profile.phone", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "date_joined",
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