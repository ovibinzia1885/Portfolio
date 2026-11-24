from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactForm


def contact(request):
    """GET: standalone contact page. POST: validate, store, show message."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if not form.is_spam():  # bots get a fake success, nothing is stored
                form.save()
            messages.success(
                request, "Thank you! Your message has been sent. I will reply soon."
            )
            return redirect(f"{reverse('core:home')}#contact")
        messages.error(request, "Please correct the errors below and try again.")
    else:
        form = ContactForm()
    return render(request, "contact/contact.html", {"form": form})
