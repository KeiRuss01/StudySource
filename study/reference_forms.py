from django import forms

from .models import ResearchFolder


class SaveExternalReferenceForm(forms.Form):
    provider = forms.ChoiceField(
        choices=(
            ("crossref", "Crossref"),
            ("google_books", "Google Books"),
        ),
        widget=forms.HiddenInput(),
    )

    external_id = forms.CharField(
        max_length=255,
        widget=forms.HiddenInput(),
    )

    folder = forms.ModelChoiceField(
        queryset=ResearchFolder.objects.none(),
        required=False,
        empty_label="Save without a folder",
        widget=forms.Select(
            attrs={
                "class": "save-reference-select",
            }
        ),
    )

    return_query = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.HiddenInput(),
    )

    return_page = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.HiddenInput(),
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

        if owner:
            self.fields["folder"].queryset = (
                ResearchFolder.objects.filter(
                    owner=owner
                )
            )