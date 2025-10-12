from smtplib import SMTP
from email.mime.text import MIMEText
import jwt
from datetime import datetime, timedelta, timezone


def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@example.com'
    msg['To'] = to

    with SMTP('maildev', 1025) as server:
        server.send_message(msg)

def generate_reset_token(user_id, secret_key, expires_in=3600):
    exp = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode({'user_id': user_id, 'exp': exp}, secret_key, algorithm='HS256')
    return token

def verify_reset_token(token, secret_key):
    try:
        data = jwt.decode(token, secret_key, algorithms=['HS256'])
        return data['user_id']
    except:
        return None