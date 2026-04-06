from django.db import migrations


def create_admin_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Admin")
    # To avoid creating groups through the Django admin panel or programmatically


def delete_admin_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("specialties", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin_group, reverse_code=delete_admin_group),
    ]