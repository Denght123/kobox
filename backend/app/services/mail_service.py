from email.message import EmailMessage
import smtplib
import ssl

from app.core.config import Settings
from app.core.exceptions import AppException


class MailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from_email)

    def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        if not self.is_configured:
            if self.settings.app_env == "development":
                return
            raise AppException(status_code=503, code="mail_not_configured", message="Password reset email is not configured")

        message = EmailMessage()
        message["Subject"] = "Kobox password reset"
        message["From"] = self.settings.smtp_from_email
        message["To"] = to_email
        message.set_content(
            "Use this link to reset your Kobox password. "
            "If you did not request this, you can ignore this email.\n\n"
            f"{reset_url}\n"
        )

        context = ssl.create_default_context()
        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, context=context, timeout=10) as server:
                self._login(server)
                server.send_message(message)
            return

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as server:
            if self.settings.smtp_use_tls:
                server.starttls(context=context)
            self._login(server)
            server.send_message(message)

    def _login(self, server: smtplib.SMTP) -> None:
        if self.settings.smtp_username and self.settings.smtp_password:
            server.login(self.settings.smtp_username, self.settings.smtp_password)
