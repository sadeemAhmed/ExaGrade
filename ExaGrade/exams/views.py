from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string

from users.models import CustomUser
from .models import Exam, Grade, StudentPaper
from courses.models import Course
from .forms import ExamForm
from django.contrib import messages

@login_required
def exam_list_view(request):
    if request.user.is_instructor:
        exams = Exam.objects.filter(course__in=request.user.courses.all())  
    else:
        exams = Exam.objects.filter(course__in=request.user.enrolled_courses.all())

    return render(request, "exams/exam_list.html", {"exams": exams})

@login_required
def exam_detail_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.is_student and exam.course not in request.user.enrolled_courses.all():
        return redirect("exams:list")  

    return render(request, "exams/exam_detail.html", {"exam": exam})

@login_required
def grade_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Ensure only instructors can grade
    if not request.user.is_instructor:
        messages.error(request, "⚠️ You are not authorized to grade this exam.")
        return redirect("exams:detail", exam_id=exam.id)

    # Add grading logic here (e.g., OCR processing, AI grading, or manual grading)

    return render(request, "exams/grade_exam.html", {"exam": exam})

@login_required
def exam_students_grades(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    grades = Grade.objects.filter(exam=exam)  # Get all grades for this exam

    return render(request, "exams/exam_students_grades.html", {
        "exam": exam,
        "grades": grades
    })

@login_required
def student_grades_view(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id)
    grades = Grade.objects.filter(student=student)  # Get all grades for this student

    return render(request, "exams/student_grades.html", {"student": student, "grades": grades})

@login_required
def add_exam(request):
    if not request.user.is_instructor:
        return redirect("exams:list") 

    if request.method == "POST":
        form = ExamForm(request.POST, request.FILES)

        course_id = request.POST.get("course_id")
        if not course_id:
            messages.error(request, "⚠️ Please select a course before creating an exam.")
            return redirect("exams:add")

        try:
            course = Course.objects.get(id=course_id, instructor=request.user)
        except Course.DoesNotExist:
            messages.error(request, "❌ The selected course does not exist or you don't have access to it.")
            return redirect("exams:add")

        if form.is_valid():
            exam = form.save(commit=False)
            exam.course = course
            exam.instructor = request.user
            exam.exam_code = get_random_string(6).upper()
            exam.save()
            messages.success(request, f"🎉 Exam '{exam.name}' added successfully!")
            return redirect("exams:list")
        else:
            messages.error(request, "⚠️ Please fix the errors in the form.")

    else:
        form = ExamForm()

    courses = Course.objects.filter(instructor=request.user)
    return render(request, "exams/add_exam.html", {"form": form, "courses": courses})