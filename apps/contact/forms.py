from django import forms

from .models import ContactMessage

MAX_MESSAGE_LENGTH = 5000


class ContactForm(forms.ModelForm):
    # Honeypot: real visitors never see/fill this; bots usually do.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off",
    }))

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"placeholder": "What is this about?"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Write your message..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs["class"] = "form-control"

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return name

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise forms.ValidationError(
                f"Message is too long (maximum {MAX_MESSAGE_LENGTH} characters)."
            )
        return message

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
