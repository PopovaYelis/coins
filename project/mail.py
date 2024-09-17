import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from config import SMTP_HOST, SMTP_PORT, SMTP_PASSWORD, SMTP_USER


def send_email(recipient, filename):
    """
    """
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)

        email = MIMEMultipart()
        email['Subject'] = f'Ooooh!!! The exchange rate has skyrocketed!'
        email['From'] = SMTP_USER
        email['To'] = recipient

        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={filename}'
        )
        email.attach(part)
        text = email.as_string()


        server.sendmail(SMTP_USER, recipient, text)

