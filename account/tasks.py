import ssl
import smtplib
from django.conf import settings
from email.message import EmailMessage
from email.utils import formataddr
from celery import shared_task


@shared_task
def send_html_email_task(receiver, subject, body):
    sender = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    
    em = EmailMessage()
    em['From'] = formataddr(("SEC Results", sender))
    em['To'] = receiver
    em['Subject'] = subject
    em.set_content(body, subtype='html')
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host, port, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, em.as_string())