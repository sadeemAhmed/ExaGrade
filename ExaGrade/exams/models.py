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

    def __str__(self):
        return self.name


class StudentPaper(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="student_papers")
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="submitted_papers")
    file = models.FileField(upload_to="exams/student_papers/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.name}"

class Grade(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="grades_received")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    grade = models.CharField(max_length=10)  # Can be numeric or letter grade
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.name} - {self.grade}"