# Generated by Django 5.1.3 on 2024-11-15 13:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0014_alter_user_managers_user_date_joined_user_is_staff_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='date_joined',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_login',
        ),
    ]
