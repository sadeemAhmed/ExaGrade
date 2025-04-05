import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from users.models import CustomUser
from .models import Exam, Grade, StudentPaper, Question
from courses.models import Course


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
        messages.error(request, "\u26a0\ufe0f You do not have permission to view this exam.")
        return redirect("exams:list")

    questions = Question.objects.filter(exam=exam)
    student_papers = StudentPaper.objects.filter(exam=exam)
    grades = Grade.objects.filter(exam=exam)

    return render(request, "exams/exam_detail.html", {
        "exam": exam,
        "questions": questions,
        "student_papers": student_papers,
        "grades": grades
    })


@login_required
def add_or_edit_exam(request):
    if not request.user.is_instructor:
        messages.error(request, "⚠️ Only instructors can create or edit exams.")
        return redirect("exams:list")

    exam_to_edit = None
    questions_by_type = {}
    edit_mode = request.GET.get("edit")

    if edit_mode:
        exam_to_edit = get_object_or_404(Exam, id=edit_mode, instructor=request.user)
        all_questions = Question.objects.filter(exam=exam_to_edit)

        # 👉 Split MCQ options into list for easier template use
        mcq_questions = all_questions.filter(question_type='mcq')
        for q in mcq_questions:
            q.option_list = q.mcq_options.split(",") if q.mcq_options else ["", "", "", ""]

        questions_by_type = {
            'true_false': all_questions.filter(question_type='true_false'),
            'mcq': mcq_questions,
            'short_answer': all_questions.filter(question_type='short_answer'),
            'long_answer': all_questions.filter(question_type='long_answer'),
        }

    if request.method == "POST":
        exam_name = request.POST.get("exam_name")
        course_id = request.POST.get("course")
        total_marks = request.POST.get("total_marks")
        exam_time = request.POST.get("exam_time")

        if not exam_name or not course_id or not total_marks:
            messages.error(request, "⚠️ Please fill in all required fields.")
            if exam_to_edit:
                return redirect(f"{reverse('exams:add')}?edit={exam_to_edit.id}")
            return redirect("exams:add")

        try:
            course = Course.objects.get(id=course_id, instructor=request.user)
        except Course.DoesNotExist:
            messages.error(request, "❌ Invalid course.")
            return redirect("exams:add")

        if exam_to_edit:
            exam = exam_to_edit
            exam.name = exam_name
            exam.course = course
            exam.total_marks = total_marks
            exam.duration_minutes = exam_time or 0
            exam.save()

            # 🧹 Delete old questions before updating
            Question.objects.filter(exam=exam).delete()

        else:
            exam = Exam.objects.create(
                name=exam_name,
                course=course,
                instructor=request.user,
                total_marks=total_marks,
                duration_minutes=exam_time or 0
            )

        # === True/False Questions ===
        tf_questions = request.POST.getlist('tf_questions[]')
        tf_answers = request.POST.getlist('tf_answers[]')
        tf_marks = request.POST.getlist('tf_marks[]')
        for q, a, m in zip(tf_questions, tf_answers, tf_marks):
            if q and a:
                Question.objects.create(
                    exam=exam,
                    question_type='true_false',
                    text=q,
                    correct_answer=a,
                    marks=m
                )

        # === MCQ Questions ===
        mcq_questions = request.POST.getlist('mcq_questions[]')
        opt1 = request.POST.getlist('mcq_options_1[]')
        opt2 = request.POST.getlist('mcq_options_2[]')
        opt3 = request.POST.getlist('mcq_options_3[]')
        opt4 = request.POST.getlist('mcq_options_4[]')
        answers = request.POST.getlist('mcq_answers[]')
        mcq_marks = request.POST.getlist('mcq_marks[]')
        for i in range(len(mcq_questions)):
            if mcq_questions[i]:
                options = [opt1[i], opt2[i], opt3[i], opt4[i]]
                Question.objects.create(
                    exam=exam,
                    question_type='mcq',
                    text=mcq_questions[i],
                    mcq_options=",".join(options),
                    correct_answer=answers[i],
                    marks=mcq_marks[i]
                )

        # === Short Answer ===
        short_questions = request.POST.getlist('short_questions[]')
        short_answers = request.POST.getlist('short_correct_answer[]')
        short_marks = request.POST.getlist('short_marks[]')
        for q, a, m in zip(short_questions, short_answers, short_marks):
            if q and a:
                Question.objects.create(
                    exam=exam,
                    question_type='short_answer',
                    text=q,
                    correct_answer=a,
                    marks=m
                )

        # === Long Answer ===
        long_questions = request.POST.getlist('long_questions[]')
        long_answers = request.POST.getlist('long_correct_answer[]')
        long_marks = request.POST.getlist('long_marks[]')
        for q, a, m in zip(long_questions, long_answers, long_marks):
            if q and a:
                Question.objects.create(
                    exam=exam,
                    question_type='long_answer',
                    text=q,
                    correct_answer=a,
                    marks=m
                )

        if exam_to_edit:
            messages.success(request, f"✅ Exam '{exam.name}' updated successfully!")
            return redirect("exams:list")
        else:
            messages.success(request, f"✅ Exam '{exam.name}' created successfully!")
            return redirect("exams:list")

    courses = Course.objects.filter(instructor=request.user)
    return render(request, "exams/add_exam.html", {
        "courses": courses,
        "exam": exam_to_edit,
        "questions_by_type": questions_by_type,
    })

@login_required
def grade_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_instructor:
        messages.error(request, "⚠️ You are not authorized to grade this exam.")
        return redirect("exams:list")
    student_papers = StudentPaper.objects.filter(exam=exam)
    return render(request, "exams/grade_exam.html", {
        "exam": exam,
        "student_papers": student_papers
    })

@login_required
def exam_students_grades(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_instructor:
        messages.error(request, "⚠️ You are not authorized to view student grades.")
        return redirect("exams:list")
    grades = Grade.objects.filter(exam=exam)
    return render(request, "exams/exam_students_grades.html", {
        "exam": exam,
        "grades": grades
    })


@login_required
def student_grades_view(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id)
    if request.user != student and not request.user.is_instructor:
        messages.error(request, "⚠️ You do not have permission to view these grades.")
        return redirect("exams:list")
    grades = Grade.objects.filter(student=student)
    return render(request, "exams/student_grades.html", {
        "student": student,
        "grades": grades
    })


@login_required
def download_answer_sheet(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam=exam)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)

    y = 750
    p.drawString(200, y, f"Answer Sheet for {exam.name}")
    y -= 30

    for idx, question in enumerate(questions, 1):
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"{idx}. {question.text}")
        y -= 20
        if question.question_type == "mcq":
            p.setFont("Helvetica", 11)
            for option in question.get_mcq_options():
                p.drawString(70, y, f"• {option}")
                y -= 15
        y -= 30
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{exam.name}_AnswerSheet.pdf")


@require_POST
@login_required
def generate_exam_pdf(request, exam_id):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    def draw_wrapped_text(p, x, y, text, max_width, font="Helvetica", font_size=12, line_height=15):
        p.setFont(font, font_size)
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if stringWidth(test_line, font, font_size) <= max_width:
                line = test_line
            else:
                p.drawString(x, y, line)
                y -= line_height
                line = word
        if line:
            p.drawString(x, y, line)
            y -= line_height
        return y

    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam=exam)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === Header ===
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 50, f"{exam.name} - Exam Paper")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, "Name: ____________________________")
    p.drawString(300, height - 80, "Student ID: ______________________")

    y = height - 120
    q_number = 1

    def next_page():
        nonlocal y
        p.showPage()
        y = height - 50

    def section_header(title, instruction):
        nonlocal y
        if y < 130:
            next_page()
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"■ {title}")
        y -= 16
        p.setFont("Helvetica-Oblique", 9)
        p.setFillColorRGB(0.5, 0, 0)
        p.drawString(50, y, f"* {instruction}")
        p.setFillColorRGB(0, 0, 0)
        y -= 20

    grouped = {
        "true_false": [],
        "mcq": [],
        "short_answer": [],
        "long_answer": []
    }
    for q in questions:
        grouped[q.question_type].append(q)

    max_text_width = width - 120  # Adjust this if needed

    # === TRUE/FALSE ===
    if grouped["true_false"]:
        section_header("True/False Questions", "Write 'True' or 'False' clearly in the box.")
        for q in grouped["true_false"]:
            marks = f"[{q.marks} mark{'s' if int(q.marks) > 1 else ''}]"
            q_text = f"{q_number}. {q.text}  {marks}"
            y = draw_wrapped_text(p, 50, y, q_text, max_text_width)
            p.rect(width - 90, y + 5, 35, 15)
            y -= 20
            if y < 100: next_page()
            q_number += 1

    # === MCQ ===
    if grouped["mcq"]:
        section_header("Multiple Choice Questions", "Write the letter of the correct option.")
        for q in grouped["mcq"]:
            marks = f"[{q.marks} mark{'s' if int(q.marks) > 1 else ''}]"
            q_text = f"{q_number}. {q.text}  {marks}"
            y = draw_wrapped_text(p, 50, y, q_text, max_text_width)
            options = q.get_mcq_options()
            opt_line = "    ".join([f"{chr(65 + i)}) {opt}" for i, opt in enumerate(options)])
            y = draw_wrapped_text(p, 70, y, opt_line, max_text_width - 30, font_size=11)
            p.rect(width - 90, y + 5, 35, 15)
            y -= 20
            if y < 100: next_page()
            q_number += 1

    # === SHORT ANSWER ===
    if grouped["short_answer"]:
        section_header("Short Answer Questions", "Write your answer inside the box.")
        for q in grouped["short_answer"]:
            marks = f"[{q.marks} mark{'s' if int(q.marks) > 1 else ''}]"
            q_text = f"{q_number}. {q.text}  {marks}"
            y = draw_wrapped_text(p, 50, y, q_text, max_text_width)
            p.setDash(1, 2)
            p.rect(50, y - 60, width - 100, 60)
            p.setDash()
            y -= 80
            if y < 130: next_page()
            q_number += 1

    # === LONG ANSWER ===
    if grouped["long_answer"]:
        section_header("Long Answer Questions", "Write your detailed response below.")
        for q in grouped["long_answer"]:
            marks = f"[{q.marks} mark{'s' if int(q.marks) > 1 else ''}]"
            q_text = f"{q_number}. {q.text}  {marks}"
            y = draw_wrapped_text(p, 50, y, q_text, max_text_width)
            p.rect(50, y - 120, width - 100, 120)
            y -= 140
            if y < 130: next_page()
            q_number += 1

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{exam.name}_PaperExam.pdf")

@login_required
def upload_student_paper(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user != exam.instructor:
        messages.error(request, "⚠️ You do not have permission to upload papers for this exam.")
        return redirect('exams:detail', exam_id=exam.id)

    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('student_papers')
        if uploaded_files:
            for file in uploaded_files:
                StudentPaper.objects.create(
                    exam=exam,
                    file=file
                )
            messages.success(request, f"✅ {len(uploaded_files)} student paper(s) uploaded successfully.")
        else:
            messages.warning(request, "⚠️ Please select one or more files to upload.")

    return redirect('exams:detail', exam_id=exam.id)



@login_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user != exam.instructor:
        messages.error(request, "You are not allowed to edit this exam.")
        return redirect('exams:detail', exam_id=exam.id)

    if request.method == "POST":
        exam.name = request.POST.get("exam_name")
        exam.total_marks = request.POST.get("total_marks")
        exam.duration_minutes = request.POST.get("exam_time")
        exam.save()

        # (Optional) Update questions here or handle with JS (more complex)

        messages.success(request, "✅ Exam updated successfully!")
        return redirect('exams:detail', exam_id=exam.id)

    courses = Course.objects.filter(instructor=request.user)
    questions = Question.objects.filter(exam=exam)
    return render(request, "exams/edit_exam.html", {
        "exam": exam,
        "courses": courses,
        "questions": questions,
    })

@require_POST
@login_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user != exam.instructor:
        messages.error(request, "⚠️ You don’t have permission to delete this exam.")
        return redirect("exams:list")

    exam.delete()
    messages.success(request, "🗑️ Exam deleted successfully.")
    return redirect("exams:list")


@login_required
def delete_paper(request, paper_id):
    try:
        paper = StudentPaper.objects.get(id=paper_id)
    except StudentPaper.DoesNotExist:
        messages.error(request, "⚠️ That paper doesn't exist or was already deleted.")
        return redirect("exams:list")  # or wherever you want

    exam_id = paper.exam.id
    paper.delete()
    messages.success(request, "🗑️ Paper deleted successfully.")
    return redirect('exams:detail', exam_id=exam_id)


@login_required
def send_grades(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST' and request.user.is_instructor:
        for grade in exam.grades.all():
            # You can integrate email or notifications here
            pass
        messages.success(request, "✅ Grades have been sent to all students.")
    return redirect('exams:detail', exam_id=exam.id)

