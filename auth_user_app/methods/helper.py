from django.core.mail import send_mail
from blog import settings

def send_to_mail(request, address, message):
    message = f"Hello, {email},n\n\{message}"
    subject = "Confirmation code"
    address = address
    send_mail(subject, message, settings.EMAIL_HOST_USER, [address])