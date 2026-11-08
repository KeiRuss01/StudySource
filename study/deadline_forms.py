from django import forms

from .models import ResearchDeadline, ResearchFolder


class ResearchDeadlineForm(forms.ModelForm):
    folder = forms.ModelChoiceField(
        queryset=ResearchFolder.objects.none(),
        label="Research folder",
    )

    class Meta:
        model = ResearchDeadline
        fields = (
            "folder",
            "title",
            "description",
            "due_date",
        )
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Example: Submit literature review",
                "autocomplete": "off",
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Optional details about this deadline.",
                "rows": 5,
            }),
            "due_date": forms.DateInput(attrs={
                "type": "date",
            }),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner:
            self.fields["folder"].queryset = ResearchFolder.objects.filter(
                owner=owner
            )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Please enter a deadline title.")
        return title
