from django import forms

from .models import ResearchNote, SavedReference


class ResearchNoteForm(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        label="Note title",
        widget=forms.TextInput(
            attrs={
                "placeholder": (
                    "Example: Key findings from the paper"
                ),
                "autocomplete": "off",
            }
        ),
    )

    content = forms.CharField(
        label="Note content",
        widget=forms.Textarea(
            attrs={
                "placeholder": (
                    "Write your own research notes here."
                ),
                "rows": 12,
            }
        ),
    )

    saved_reference = forms.ModelChoiceField(
        queryset=SavedReference.objects.none(),
        required=False,
        empty_label="No linked reference",
        label="Linked reference",
    )

    class Meta:
        model = ResearchNote

        fields = (
            "title",
            "content",
            "saved_reference",
        )

    def __init__(
        self,
        *args,
        owner=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.owner = owner

        if owner:
            self.fields[
                "saved_reference"
            ].queryset = (
                SavedReference.objects.filter(
                    owner=owner
                )
            )

    def clean_title(self):
        title = (
            self.cleaned_data["title"]
            .strip()
        )

        if not title:
            raise forms.ValidationError(
                "Please enter a note title."
            )

        return title

    def clean_content(self):
        content = (
            self.cleaned_data["content"]
            .strip()
        )

        if not content:
            raise forms.ValidationError(
                "Please write some note content."
            )

        return content