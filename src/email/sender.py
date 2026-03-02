"""Gmail SMTP email sender."""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(html_body: str, subject: str) -> None:
    """
    Send an HTML email via Gmail SMTP (TLS on port 587).

    Reads configuration from environment variables:
        EMAIL_HOST  — SMTP server (default smtp.gmail.com)
        EMAIL_PORT  — SMTP port   (default 587)
        EMAIL_USER  — Gmail username / sender address
        EMAIL_PASS  — Gmail App Password
        EMAIL_FROM  — From address (defaults to EMAIL_USER)
        EMAIL_TO    — Recipient address
    """
    host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_PORT", "587"))
    user = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    sender = os.environ.get("EMAIL_FROM", user)
    recipient = os.environ["EMAIL_TO"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, password)
        smtp.sendmail(sender, [recipient], msg.as_string())

    logger.info("Email sent to %s — subject: %s", recipient, subject)
