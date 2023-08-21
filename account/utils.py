from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import FileExtensionValidator
from django.template.loader import render_to_string
from django.urls import reverse
from pathlib import Path
from PIL import Image
from io import BytesIO
from email.message import EmailMessage
from email.utils import formataddr
import ssl
import smtplib
from urllib.parse import urlencode

def send_html_email(receiver, subject, body):
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


def send_signup_email(request, invitation):
    email_subject = "Signup Invitation"
    receiver = invitation.user_email
    app_admin_signup = request.build_absolute_uri(reverse("account:signupadmin"))
    url_params = {"token":invitation.id}
    signup_url = f"{app_admin_signup}?{urlencode(url_params)}"
    email_body = render_to_string('account/invitation.html', context={
        "signup_url": signup_url,
        "invitation": invitation
    })
    send_html_email(receiver, email_subject, email_body)
    


def validate_image_extension(value):
    valid_extensions = map(lambda f: "."+f, settings.ALLOWED_IMAGE_EXTENSIONS) # adding a dot(.) before extension
    ext = Path(value.name).suffix
    if not ext.lower() in valid_extensions:
        raise ValidationError('Invalid file type. Allowed file types are: {}'.format(', '.join(valid_extensions)))
    
    
def compress_image(image):
    try:
        validate_image_extension(image)
    except ValidationError:
        raise ValidationError("Invalid image file")
    img = Image.open(image)
    width, height = img.size
    # Calculate the dimensions of the center portion to be cropped
    crop_width = crop_height = min(width, height)

    # Calculate the left, upper, right, and lower coordinates of the center portion
    left = (width - crop_width) // 2
    upper = (height - crop_height) // 2
    right = left + crop_width
    lower = upper + crop_height

    # Crop the center portion of the image
    center_cropped_image = img.crop((left, upper, right, lower))
    formatted_img = center_cropped_image.resize((500,500))
    img_format = img.format.lower()
    img_io = BytesIO()
    formatted_img.save(img_io, format=img_format, quality=50)
    img_file = ContentFile(img_io.getvalue())

    if hasattr(image, 'name') and image.name:
        img_file.name = image.name

    if hasattr(image, 'content_type') and image.content_type:
        img_file.content_type = image.content_type

    if hasattr(image, 'size') and image.size:
        img_file.size = image.size

    if hasattr(image, 'charset') and image.charset:
        img_file.charset = image.charset

    if hasattr(image, '_committed') and image._committed:
        img_file._committed = image._committed

    return img_file