# Generated by Django 5.0.1 on 2024-03-06 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0013_rename_leadername_participants_firstname_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participants',
            name='lastname',
            field=models.CharField(default='-', max_length=255),
        ),
    ]
