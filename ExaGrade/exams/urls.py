from django.urls import path
from . import views

app_name = "exams"

urlpatterns = [
    path("", views.exam_list_view, name="list"),
    path("add/", views.add_or_edit_exam, name="add"),
    path("<int:exam_id>/", views.exam_detail_view, name="detail"),  # ✅ only this
    path("<int:exam_id>/edit/", views.edit_exam, name="edit_exam"),
    path("<int:exam_id>/delete/", views.delete_exam, name="delete_exam"),
    path("<int:exam_id>/grade/", views.grade_exam, name="grade_exam"),
    path("<int:exam_id>/grades/", views.exam_students_grades, name="exam_students_grades"),
    path("student/<int:student_id>/grades/", views.student_grades_view, name="student_grades"),
    path("<int:exam_id>/generate-paper/", views.generate_exam_pdf, name="generate_exam_pdf"),
    path("<int:exam_id>/upload-student-paper/", views.upload_student_paper, name="upload_student_paper"),
    path("paper/delete/<int:paper_id>/", views.delete_paper, name="delete_paper"),
    path("<int:exam_id>/send-grades/", views.send_grades, name="send_grades"),
]