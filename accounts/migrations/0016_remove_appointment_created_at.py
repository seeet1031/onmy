# Generated by Django 5.0.7 on 2024-08-18 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_rename_date_appointment_appointment_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appointment',
            name='created_at',
        ),
    ]
