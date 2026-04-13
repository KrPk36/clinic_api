from django.db import migrations


def create_doctor_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Doctor")

def delete_doctor_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Doctor").delete()


def create_patient_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Patient")

def delete_patient_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Patient").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_doctor_group, reverse_code=delete_doctor_group),
        migrations.RunPython(create_patient_group, reverse_code=delete_patient_group),
    ]