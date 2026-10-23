from django import forms


class ResearchImageForm(forms.Form):
    title = forms.CharField(
        max_length=150,
        required=False,
        label="Image title",
        widget=forms.TextInput(attrs={
            "placeholder": "Example: Handwritten lecture notes",
        }),
    )
    image = forms.ImageField(
        label="Image file",
        help_text="PNG, JPG, or WEBP up to 10 MB.",
    )

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Images must be 10 MB or smaller.")
        return image
