from django.urls import path
from . import views

app_name = "electronic_exams"

urlpatterns = [
    path("", views.ExamListView.as_view(), name="exam_list"),
    path("create/", views.CreateExamView.as_view(), name="create"),
    path("create/<int:pk>/", views.CreateExamView.as_view(), name="edit_exam"),
    path("<int:pk>/", views.ExamDetailView.as_view(), name="exam_detail"),
    path("<int:pk>/results/", views.ExamResultsView.as_view(), name="exam_results"),
    path("<int:pk>/take/", views.TakeExamView.as_view(), name="take_exam"),
    path("question/<int:question_id>/delete/", views.DeleteQuestionView.as_view(), name="delete_question"),
    path("<int:pk>/toggle/", views.ToggleExamView.as_view(), name="toggle_exam"),
    path("question/<int:pk>/update/", views.UpdateQuestionView.as_view(), name="update_question"),
    path("<int:pk>/delete/", views.DeleteExamView.as_view(), name="delete_exam"),
]
