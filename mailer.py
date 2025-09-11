# mailer.py
import smtplib, hmac, hashlib, base64, yaml
from email.mime.text import MIMEText
from email.utils import formataddr

def _load_secret() -> bytes:
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            sec = cfg.get("secret", "CHANGE_ME_SECRET")
            return sec.encode()
    except Exception:
        return b"CHANGE_ME_SECRET"

def make_token(task_id: int) -> str:
    secret = _load_secret()
    digest = hmac.new(secret, str(task_id).encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")

def build_task_url(base_url: str, token: str):
    return f"{base_url}/complete?token={token}"

def send_email(smtp_host, smtp_port, smtp_id, smtp_pw, sender_name, sender_email, to_email, subject, html_body):
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to_email

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
        s.login(smtp_id, smtp_pw)
        s.sendmail(sender_email, [to_email], msg.as_string())
