# Generated by Django 5.1.6 on 2025-02-19 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_alter_user_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excel',
            name='file',
            field=models.FileField(upload_to='excel'),
        ),
    ]
