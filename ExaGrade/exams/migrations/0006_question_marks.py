# Generated by Django 5.1.5 on 2025-04-02 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0005_remove_grade_question_exam_duration_minutes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='marks',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
