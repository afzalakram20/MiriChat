# app/services/email_service.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple
import mimetypes
import base64
import os
import logging

from app.core.config import settings

log = logging.getLogger("app.services.email")

class EmailService:
    def __init__(self):
        self.provider = (settings.EMAIL_PROVIDER or "smtp").lower()

    def _guess_mime(self, file_path: Path) -> Tuple[str, str]:
        mt, _ = mimetypes.guess_type(str(file_path))
        if not mt:
            return ("application", "octet-stream")
        major, minor = mt.split("/", 1)
        return (major, minor)

    def send_with_attachment(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        file_path: str,
        from_email: Optional[str] = None,
    ) -> bool:
        from_email = from_email or settings.EMAIL_FROM
        path = Path(file_path)
        log.error("send_with_attachment: %s", path)
        if not path.exists():
            log.error("Attachment not found: %s", path)
            return False

        if self.provider == "ses":
            return self._send_via_ses(to_email, subject, body_text, path, from_email)
        else:
            return self._send_via_smtp(to_email, subject, body_text, path, from_email)

    # ---------- SMTP ----------
    def _send_via_smtp(self, to_email: str, subject: str, body_text: str, path: Path, from_email: str) -> bool:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body_text)
        log.info("here in _send_via_smtp")
        log.info(f"here in msg{msg}")
        major, minor = self._guess_mime(path)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=major, subtype=minor, filename=path.name)

        try:
            if settings.SMTP_USE_TLS:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                    s.starttls()
                    if settings.SMTP_USERNAME:
                        s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    s.send_message(msg)
            else:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                    if settings.SMTP_USERNAME:
                        s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    s.send_message(msg)
            log.info("SMTP email sent to %s with attachment %s", to_email, path.name)
            return True
        except Exception as e:
            log.exception("SMTP send failed: %s", e)
            return False

    # ---------- AWS SES ----------
    def _send_via_ses(self, to_email: str, subject: str, body_text: str, path: Path, from_email: str) -> bool:
        import boto3
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, "plain"))

        major, minor = self._guess_mime(path)
        part = MIMEBase(major, minor)
        with open(path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
        msg.attach(part)

        try:
            ses = boto3.client(
                "ses",
                region_name=settings.AWS_SES_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            ses.send_raw_email(
                Source=from_email,
                Destinations=[to_email],
                RawMessage={"Data": msg.as_string()},
            )
            log.info("SES email sent to %s with attachment %s", to_email, path.name)
            return True
        except Exception as e:
            log.exception("SES send failed: %s", e)
            return False
