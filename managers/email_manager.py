"""SMTP delivery for sending VPN configs to users.

This module is the only place that talks to an external SMTP server. Settings
come from data.json (settings.email), set via the panel's Settings UI — there
are no env-var overrides on purpose, because the admin should be able to swap
SMTP providers without rebuilding the container.
"""
from __future__ import annotations

import io
import logging
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Optional, Tuple

import aiosmtplib

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    # MIME type as "main/sub", e.g. ("application", "octet-stream") or ("image", "png").
    mime_main: str = "application"
    mime_sub: str = "octet-stream"


@dataclass
class SMTPSettings:
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = ""
    # "starttls" (port 587), "ssl" (port 465 implicit TLS), "none" (plain).
    encryption: str = "starttls"

    @classmethod
    def from_dict(cls, d: dict) -> "SMTPSettings":
        return cls(
            host=str(d.get("host") or "").strip(),
            port=int(d.get("port") or 587),
            username=str(d.get("username") or "").strip(),
            password=str(d.get("password") or ""),
            from_email=str(d.get("from_email") or "").strip(),
            from_name=str(d.get("from_name") or "").strip(),
            encryption=str(d.get("encryption") or "starttls").lower().strip(),
        )

    def is_configured(self) -> bool:
        # We don't require username/password — some internal relays accept
        # unauthenticated mail. host + from_email is the bare minimum.
        return bool(self.host and self.from_email)


def _build_message(
    settings: SMTPSettings,
    to_email: str,
    subject: str,
    body: str,
    attachments: List[EmailAttachment],
) -> EmailMessage:
    msg = EmailMessage()
    from_header = (
        f"{settings.from_name} <{settings.from_email}>"
        if settings.from_name
        else settings.from_email
    )
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Subject"] = subject or "Your VPN configuration"
    msg.set_content(body or "")

    for att in attachments:
        msg.add_attachment(
            att.content,
            maintype=att.mime_main,
            subtype=att.mime_sub,
            filename=att.filename,
        )
    return msg


async def send_email(
    settings: SMTPSettings,
    to_email: str,
    subject: str,
    body: str,
    attachments: Optional[List[EmailAttachment]] = None,
) -> Tuple[bool, str]:
    """Send one email asynchronously. Returns (ok, message). Never raises —
    the caller surfaces the message back to the admin via the API response."""
    if not settings.is_configured():
        return False, "SMTP is not configured (open Settings → Email)"
    if not to_email:
        return False, "Recipient email is empty"

    msg = _build_message(settings, to_email, subject, body, attachments or [])

    use_ssl = settings.encryption == "ssl"
    start_tls = settings.encryption == "starttls"
    tls_context = ssl.create_default_context() if (use_ssl or start_tls) else None

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.host,
            port=settings.port,
            username=settings.username or None,
            password=settings.password or None,
            use_tls=use_ssl,            # implicit TLS (e.g. port 465)
            start_tls=start_tls,        # STARTTLS handshake on plain socket
            tls_context=tls_context,
            timeout=30,
        )
        return True, "ok"
    except Exception as e:
        logger.exception("SMTP send failed to %s", to_email)
        return False, f"{type(e).__name__}: {e}"


def render_qr_png(text: str, box_size: int = 8, border: int = 2) -> bytes:
    """Render the given text as a PNG QR code. Used by the email-config
    flow to attach a scannable QR alongside the .conf file. We do not
    pre-chunk here — chunked-QR for AmneziaWG happens elsewhere and isn't
    suitable for a single emailed image."""
    import qrcode  # local import — only loaded when an admin actually emails

    img = qrcode.make(text, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
