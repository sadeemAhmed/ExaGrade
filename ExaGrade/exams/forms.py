from django import forms
from .models import Exam, StudentPaper



class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["name", "student_paper", "solution_module"] 
        widgets = {
            "name": forms.TextInput(attrs={"class": "border rounded-lg px-4 py-2 w-full", "required": True}),
            "student_paper": forms.ClearableFileInput(attrs={"class": "border rounded-lg px-4 py-2 w-full"}),
            "solution_module": forms.ClearableFileInput(attrs={"class": "border rounded-lg px-4 py-2 w-full"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("name"):
            self.add_error("name", "Exam name is required.")
        return cleaned_data