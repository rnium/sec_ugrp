# Generated by Django 4.2.3 on 2024-02-08 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0039_semester_exam_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_carry_course',
            field=models.BooleanField(default=False),
        ),
    ]