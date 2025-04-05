# Generated by Django 5.1.5 on 2025-04-02 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0004_question_answer_grade_question'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grade',
            name='question',
        ),
        migrations.AddField(
            model_name='exam',
            name='duration_minutes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exam',
            name='total_marks',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Answer',
        ),
    ]
