"""
PEPR Email Service
Sends transactional emails (password reset codes, notifications) via SMTP.
Uses Python's built-in smtplib — no extra dependencies required.
"""
import asyncio
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("pepr.email")

# ── Config from environment ────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "PEPR Pakistan Economics Problem Radar")


def _build_reset_email_html(full_name: str, reset_code: str) -> str:
    """Returns a professional HTML email body for password reset."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Password Reset — PEPR</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(11,37,69,0.12);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0B2545 0%,#005A36 100%);
                       padding:32px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                         letter-spacing:0.5px;">
                🔐 Password Reset Request
              </h1>
              <p style="margin:6px 0 0;color:#a7c4ad;font-size:13px;">
                Pakistan Economics Problem Radar (PEPR)
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <p style="margin:0 0 16px;color:#334155;font-size:15px;line-height:1.6;">
                Hello <strong>{full_name}</strong>,
              </p>
              <p style="margin:0 0 24px;color:#334155;font-size:15px;line-height:1.6;">
                We received a request to reset your PEPR researcher account password.
                Use the verification code below to proceed:
              </p>

              <!-- Code box -->
              <div style="background:#f8fafc;border:2px dashed #005A36;border-radius:10px;
                          padding:28px;text-align:center;margin:0 0 28px;">
                <p style="margin:0 0 8px;color:#64748b;font-size:12px;
                           text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">
                  Your Verification Code
                </p>
                <span style="font-size:42px;font-weight:800;letter-spacing:12px;
                             color:#0B2545;font-family:'Courier New',monospace;">
                  {reset_code}
                </span>
              </div>

              <p style="margin:0 0 12px;color:#334155;font-size:14px;line-height:1.6;">
                ⏱ This code is valid for <strong>15 minutes</strong>.
              </p>
              <p style="margin:0 0 24px;color:#64748b;font-size:13px;line-height:1.6;">
                If you did not request a password reset, please ignore this email.
                Your account remains secure — no changes have been made.
              </p>

              <hr style="border:none;border-top:1px solid #e2e8f0;margin:0 0 24px;" />

              <p style="margin:0;color:#94a3b8;font-size:12px;text-align:center;">
                This is an automated message from the PEPR system.<br/>
                Pakistan Institute of Development Economics (PIDE)
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f8fafc;padding:16px 40px;text-align:center;
                       border-top:1px solid #e2e8f0;">
              <p style="margin:0;color:#94a3b8;font-size:11px;">
                © 2026 PIDE — Pakistan Institute of Development Economics
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _send_smtp_blocking(to_email: str, to_name: str, reset_code: str) -> None:
    """Blocking SMTP send — called via asyncio executor to avoid blocking the event loop."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "PEPR Pakistan Economics Problem Radar")

    if not smtp_user or smtp_password in ("", "your_app_password_here"):
        # Dev fallback: just log the code so development still works
        logger.warning(
            "[EMAIL-DEV] SMTP not configured. Reset code for %s → %s",
            to_email, reset_code
        )
        return

    subject = "PEPR — Your Password Reset Code"
    from_addr = f"{smtp_from_name} <{smtp_user}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = f"{to_name} <{to_email}>"

    plain_text = (
        f"Hello {to_name},\n\n"
        f"Your PEPR password reset verification code is: {reset_code}\n\n"
        f"This code expires in 15 minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— PEPR / PIDE Team"
    )
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(_build_reset_email_html(to_name, reset_code), "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

    logger.info("[EMAIL] Password reset code sent successfully to %s", to_email)


async def send_reset_code_email(to_email: str, to_name: str, reset_code: str) -> bool:
    """
    Async wrapper — runs SMTP send in a thread pool so it does not block FastAPI.
    Returns True on success, False on failure (logs the error).
    """
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            partial(_send_smtp_blocking, to_email, to_name, reset_code)
        )
        return True
    except Exception as exc:
        logger.error(
            "[EMAIL] Failed to send reset code to %s: %s", to_email, exc, exc_info=True
        )
        return False
