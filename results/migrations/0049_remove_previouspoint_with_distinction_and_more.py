# Generated by Django 4.2.3 on 2024-03-22 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0048_remove_semester_unique_session_semester_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='previouspoint',
            name='with_distinction',
        ),
        migrations.AddField(
            model_name='studentpoint',
            name='with_distinction',
            field=models.BooleanField(default=False),
        ),
    ]