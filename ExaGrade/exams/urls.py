from django.urls import path
from .views import exam_detail_view, exam_list_view, add_exam, exam_students_grades, grade_exam, student_grades_view

app_name = "exams"

urlpatterns = [
    path("", exam_list_view, name="list"),
    path("<int:exam_id>/", exam_detail_view, name="detail"),
    path("add/", add_exam, name="add"),
    path("<int:exam_id>/grade/", grade_exam, name="grade_exam"),
    path("<int:exam_id>/grades/", exam_students_grades, name="exam_students_grades"),
    path("student/<int:student_id>/grades/", student_grades_view, name="student_grades"),
]

