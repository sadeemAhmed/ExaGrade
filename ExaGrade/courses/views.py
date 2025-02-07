from django.shortcuts import render, get_object_or_404, redirect
from .models import Course
from exams.models import Exam, Grade
from .forms import CourseForm
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def course_list(request):
    if request.user.is_instructor:
        courses = Course.objects.filter(instructor=request.user)
    else:
        courses = request.user.enrolled_courses.all()

    if request.method == "POST" and request.user.is_instructor:
        name = request.POST.get("name")
        description = request.POST.get("description")
        course_code = get_random_string(6).upper()
        Course.objects.create(name=name, description=description, instructor=request.user, course_code=course_code)
        return redirect("courses:list")

    return render(request, "courses/course_list.html", {"courses": courses})

@login_required
def enroll_course(request):
    if request.method == "POST":
        course_code = request.POST.get("course_code")
        course = get_object_or_404(Course, course_code=course_code)
        request.user.enrolled_courses.add(course)
        messages.success(request, f"🎓 You have successfully joined {course.name}!")
        return redirect("courses:detail", course_id=course.id)
    return render(request, "users/enroll_course.html")

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    exams = Exam.objects.filter(course=course)

    # Ensure enrolled students are fetched only for instructors
    students = course.students.all() if request.user.is_instructor else None

    # Fetch grades - only the student's own grades if they are a student
    if request.user.is_student:
        for exam in exams:
            exam.grades = Grade.objects.filter(exam=exam, student=request.user)  # Fetch only their grades
    else:
        for exam in exams:
            exam.grades = Grade.objects.filter(exam=exam)  # Fetch all grades for instructors

    return render(request, "courses/course_detail.html", {
        "course": course,
        "exams": exams,
        "students": students  # Pass students list to the template
    })


@login_required
def delete_course(request, course_id):
    # Use `get_object_or_404` to ensure a valid course is retrieved or return 404
    course = get_object_or_404(Course, id=course_id)

    # Ensure only the instructor can delete the course
    if request.user != course.instructor:
        messages.error(request, "You are not authorized to delete this course.")
        return redirect("courses:detail", course_id=course.id)

    # Delete the course
    course.delete()
    messages.success(request, "Course deleted successfully.")
    
    # Redirect back to the courses list
    return redirect("courses:list")

@login_required
def add_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user  # Assign instructor
            course.save()
            messages.success(request, "✅ Course added successfully!")
            return redirect("courses:list")  # Redirect to course list
        else:
            messages.error(request, "⚠️ Please fill in all required fields.")
    else:
        form = CourseForm()
    return render(request, "courses/add_course.html", {"form": form})

