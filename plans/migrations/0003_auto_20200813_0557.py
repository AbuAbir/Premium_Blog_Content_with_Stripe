# Generated by Django 3.0.8 on 2020-08-13 05:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0002_customer'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FitnessPlan',
            new_name='BlogPlan',
        ),
    ]