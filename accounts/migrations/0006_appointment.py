# Generated by Django 5.0.7 on 2024-07-27 17:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_department'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doctor', models.CharField(max_length=100)),
                ('appointment_type', models.CharField(choices=[('revisit', '再診'), ('first', '初診')], max_length=10)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('symptoms', models.TextField(blank=True, null=True)),
                ('prescription_needed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
