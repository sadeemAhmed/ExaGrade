from django.db import models
from courses.models import Course
from users.models import CustomUser

class Exam(models.Model):
    STATUS_CHOICES = [
        ("done", "Done"),
        ("progress", "Progress"),
        ("pending", "Pending"),
        ("requires_attention", "Requires Attention"),
    ]

    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="exams")
    student_paper = models.FileField(upload_to="exams/student_papers/", blank=True, null=True)
    solution_module = models.FileField(upload_to="exams/solution_modules/", blank=True, null=True)

    # ✅ Add these two lines:
    total_marks = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = [
        ("long_answer", "Long Answer"),
        ("short_answer", "Short Answer"),
        ("mcq", "Multiple Choice"),
        ("true_false", "True/False"),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    mcq_options = models.TextField(blank=True, null=True)  # Stores MCQ options as comma-separated values
    correct_answer = models.TextField(blank=True, null=True)  # Stores correct answers for auto-grading

    # ✅ Add this line
    marks = models.PositiveIntegerField(default=1)

    def get_mcq_options(self):
        return self.mcq_options.split(",") if self.mcq_options else []

    def __str__(self):
        return f"{self.exam.name} - {self.text[:50]}"

class StudentPaper(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="student_papers")
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="submitted_papers", blank=True, null=True)
    file = models.FileField(upload_to="exams/student_papers/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username if self.student else 'Unassigned'} - {self.exam.name}"


class Grade(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="grades_received")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    grade = models.CharField(max_length=10)  # Can be numeric or letter grade
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.name} - {self.grade}"
