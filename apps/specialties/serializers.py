from rest_framework import serializers

from .models import Specialty


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        """
        Case-insensitive uniqueness check so 'cardiology' and 'Cardiology'
        are treated as duplicates.
        """
        qs = Specialty.objects.filter(name__iexact=value)
        # Exclude current instance when updating
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A specialty with this name already exists.")
        return value