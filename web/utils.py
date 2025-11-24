from datetime import datetime, timedelta, timezone
from io import StringIO, BytesIO
import csv
import json
from smtplib import SMTP
from email.mime.text import MIMEText
import jwt


def code_with_prefix(prefix, order):
    return f"{prefix}-{order:03d}"

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
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def format_datetime(dt):
    if dt is None:
        return "N/A"
    return dt.strftime("%d/%m/%Y %H:%M")

def database_uri(database="example", user="root", psswd_file=None, host="db", port=3306):
    with open(psswd_file, encoding='utf-8') as f:
        password = f.read().strip()
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

def create_csv(data):
    output = StringIO()
    writer = csv.writer(output)
    for row in data:
        writer.writerow(row)
    return output.getvalue()

def create_json(data):
    json_data = json.dumps(data, indent=4)
    buffer = BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    return buffer

def import_json(file):
    data = file.read().decode('utf-8')
    return json.loads(data)
