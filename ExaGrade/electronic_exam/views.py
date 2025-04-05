from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .models import ElectronicExam, Question, Choice, StudentResponse
from courses.models import Course
from users.models import CustomUser

@method_decorator(login_required, name="dispatch")
class ExamListView(View):
    def get(self, request):
        exams = ElectronicExam.objects.all()
        return render(request, "electronic_exams/exam_list.html", {"exams": exams})


@method_decorator(login_required, name="dispatch")
class ExamDetailView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        questions = exam.questions.all()
        students = CustomUser.objects.filter(responses__question__exam=exam).distinct()
        return render(
            request,
            "electronic_exams/exam_detail.html",
            {"exam": exam, "questions": questions, "students": students}
        )


@method_decorator(login_required, name="dispatch")
class CreateExamView(View):
    def get(self, request, pk=None):
        exam = None
        questions_by_type = {
            "true_false": [],
            "mcq": [],
            "short_answer": [],
            "long_answer": [],
        }

        if pk:
            exam = get_object_or_404(ElectronicExam, pk=pk)
            questions = exam.questions.all()
            for q in questions:
                if q.question_type == "TF":
                    questions_by_type["true_false"].append(q)
                elif q.question_type == "MCQ":
                    q.option_list = [c.text for c in q.choices.all()]
                    questions_by_type["mcq"].append(q)
                elif q.question_type == "SHORT":
                    questions_by_type["short_answer"].append(q)
                elif q.question_type == "LONG":
                    questions_by_type["long_answer"].append(q)

        courses = Course.objects.all()
        return render(request, "electronic_exams/create_exam.html", {
            "courses": courses,
            "exam": exam,
            "questions_by_type": questions_by_type
        })

    def post(self, request, pk=None):
        exam_title = request.POST.get("exam_name")
        course_id = request.POST.get("course")
        total_marks = request.POST.get("total_marks")
        duration = request.POST.get("exam_time")

        if not exam_title or not course_id or not total_marks:
            messages.error(request, "Please fill in all required fields!")
            return redirect("electronic_exams:create")

        course = get_object_or_404(Course, id=course_id)

        if pk:
            exam = get_object_or_404(ElectronicExam, pk=pk)
            exam.title = exam_title
            exam.course = course
            exam.total_marks = int(total_marks)
            exam.duration_minutes = int(duration) if duration else None
            exam.save()
            exam.questions.all().delete()
        else:
            exam = ElectronicExam.objects.create(
                title=exam_title,
                course=course,
                total_marks=int(total_marks),
                duration_minutes=int(duration) if duration else None
            )

        self._process_questions(request, exam)
        messages.success(request, "Exam saved successfully!")
        return redirect("electronic_exams:exam_list")

    def _process_questions(self, request, exam):
        for question, answer, marks in zip(
            request.POST.getlist("tf_questions[]"),
            request.POST.getlist("tf_answers[]"),
            request.POST.getlist("tf_marks[]")
        ):
            Question.objects.create(
                exam=exam,
                text=question,
                question_type="TF",
                ideal_answer=answer,
                marks=int(marks)
            )

        mcq_questions = request.POST.getlist("mcq_questions[]")
        mcq_answers = request.POST.getlist("mcq_answers[]")
        mcq_options_1 = request.POST.getlist("mcq_options_1[]")
        mcq_options_2 = request.POST.getlist("mcq_options_2[]")
        mcq_options_3 = request.POST.getlist("mcq_options_3[]")
        mcq_options_4 = request.POST.getlist("mcq_options_4[]")
        mcq_marks = request.POST.getlist("mcq_marks[]")

        for i in range(len(mcq_questions)):
            options = [
                mcq_options_1[i],
                mcq_options_2[i],
                mcq_options_3[i],
                mcq_options_4[i],
            ]
            q = Question.objects.create(
                exam=exam,
                text=mcq_questions[i],
                question_type="MCQ",
                ideal_answer=mcq_answers[i],
                marks=int(mcq_marks[i])
            )
            for opt in options:
                Choice.objects.create(
                    question=q,
                    text=opt.strip(),
                    is_correct=(opt.strip() == mcq_answers[i].strip())
                )

        for question, answer, marks in zip(
            request.POST.getlist("short_questions[]"),
            request.POST.getlist("short_correct_answer[]"),
            request.POST.getlist("short_marks[]")
        ):
            Question.objects.create(
                exam=exam,
                text=question,
                question_type="SHORT",
                ideal_answer=answer,
                marks=int(marks)
            )

        for question, answer, marks in zip(
            request.POST.getlist("long_questions[]"),
            request.POST.getlist("long_correct_answer[]"),
            request.POST.getlist("long_marks[]")
        ):
            Question.objects.create(
                exam=exam,
                text=question,
                question_type="LONG",
                ideal_answer=answer,
                marks=int(marks)
            )


@method_decorator(login_required, name="dispatch")
class TakeExamView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        return render(request, "electronic_exams/take_exam.html", {"exam": exam, "questions": exam.questions.all()})

    def post(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        student = request.user

        for question in exam.questions.all():
            answer_text = request.POST.get(f"question_{question.id}", "").strip()
            correct_answer = question.ideal_answer.strip() if question.ideal_answer else None
            is_correct = (answer_text.lower() == correct_answer.lower()) if correct_answer else None
            score = 1.0 if is_correct else 0.0

            StudentResponse.objects.create(
                student=student, question=question, answer_text=answer_text, is_correct=is_correct, score=score
            )

        messages.success(request, "Exam submitted successfully!")
        return redirect("electronic_exams:exam_results", pk=exam.pk)


@method_decorator(login_required, name="dispatch")
class ExamResultsView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        student_responses = StudentResponse.objects.filter(student=request.user, question__exam=exam)
        return render(request, "electronic_exams/exam_results.html", {"exam": exam, "responses": student_responses})


@method_decorator(login_required, name="dispatch")
class EditExamView(UpdateView):
    model = ElectronicExam
    fields = ["title", "total_marks", "course"]
    template_name = "electronic_exams/edit_exam.html"
    success_url = reverse_lazy("electronic_exams:exam_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = Course.objects.all()
        return context


@method_decorator(login_required, name="dispatch")
class DeleteQuestionView(View):
    def post(self, request, question_id):
        get_object_or_404(Question, id=question_id).delete()
        return JsonResponse({"message": "Question deleted successfully!"})


@method_decorator(login_required, name="dispatch")
class ToggleExamView(View):
    def post(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        exam.is_active = not exam.is_active
        exam.save()
        return JsonResponse({"status": "success", "is_active": exam.is_active})


@method_decorator(login_required, name="dispatch")
class UpdateQuestionView(UpdateView):
    model = Question
    fields = ["text", "question_type", "ideal_answer"]
    template_name = "electronic_exams/update_question.html"

    def get_success_url(self):
        return reverse_lazy("electronic_exams:exam_detail", kwargs={"pk": self.object.exam.pk})


class DeleteExamView(View):
    def post(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        exam.delete()
        messages.success(request, "Exam deleted successfully!")
        return redirect('electronic_exams:exam_list')