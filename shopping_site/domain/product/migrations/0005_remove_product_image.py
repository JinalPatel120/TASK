# Generated by Django 5.1.3 on 2024-11-13 12:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_alter_category_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
    ]