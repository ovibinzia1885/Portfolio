from django.test import Client, TestCase
from django.urls import resolve, reverse

from apps.core.testing import AdminClientMixin

from .forms import MAX_MESSAGE_LENGTH, ContactForm
from .models import ContactMessage
from .views import contact

VALID = {"name": "Jane Recruiter", "email": "jane@example.com", "subject": "Opportunity",
         "message": "Hello, I would like to talk about a QA role."}


class ContactFormTests(TestCase):
    def test_valid_form(self):
        form = ContactForm(data=VALID)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.is_spam())

    def test_field_rules(self):
        cases = {
            "name": " J ",
            "email": "not-an-email",
            "message": "short",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                form = ContactForm(data={**VALID, field: value})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_message_length_limit(self):
        form = ContactForm(data={**VALID, "message": "x" * (MAX_MESSAGE_LENGTH + 1)})
        self.assertFalse(form.is_valid())

    def test_whitespace_is_trimmed(self):
        form = ContactForm(data={**VALID, "name": "  Jane  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Jane")


class ContactViewTests(TestCase):
    def test_url(self):
        self.assertEqual(resolve(reverse("contact:contact")).func, contact)

    def test_valid_post_saves_and_redirects(self):
        response = self.client.post(reverse("contact:contact"), VALID, follow=True)
        self.assertRedirects(response, reverse("core:home") + "#contact")
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertContains(response, "Your message has been sent")

    def test_invalid_post_shows_errors(self):
        response = self.client.post(reverse("contact:contact"), {**VALID, "email": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please correct the errors")
        self.assertFalse(ContactMessage.objects.exists())

    def test_honeypot_not_saved(self):
        self.client.post(reverse("contact:contact"), {**VALID, "website": "http://spam"})
        self.assertFalse(ContactMessage.objects.exists())

    def test_csrf_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(reverse("contact:contact"), VALID).status_code, 403)


class ContactAdminTests(AdminClientMixin, TestCase):
    def test_messages_are_read_only_and_cannot_be_added(self):
        msg = ContactMessage.objects.create(**VALID)
        self.assertEqual(self.client.get(reverse("admin:contact_contactmessage_add")).status_code, 403)
        change = reverse("admin:contact_contactmessage_change", args=[msg.pk])
        self.client.post(change, {**VALID, "message": "Tampered message text", "is_read": "on"})
        msg.refresh_from_db()
        self.assertEqual(msg.message, VALID["message"])
        self.assertTrue(msg.is_read)

    def test_search_filter_delete(self):
        msg = ContactMessage.objects.create(**VALID)
        changelist = reverse("admin:contact_contactmessage_changelist")
        self.assertContains(self.client.get(changelist, {"q": "Opportunity"}), "Jane Recruiter")
        self.assertContains(self.client.get(changelist, {"is_read__exact": "0"}), "Jane Recruiter")
        self.client.post(reverse("admin:contact_contactmessage_delete", args=[msg.pk]), {"post": "yes"})
        self.assertFalse(ContactMessage.objects.exists())

    def test_xss_in_message_escaped_in_admin_list(self):
        ContactMessage.objects.create(name="<script>alert(1)</script>", email="a@b.co", subject="s",
                                      message="long enough message")
        response = self.client.get(reverse("admin:contact_contactmessage_changelist"))
        self.assertNotContains(response, "<script>alert(1)</script>")
