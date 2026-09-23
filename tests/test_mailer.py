import pytest
from unittest.mock import patch, MagicMock
from src.mailer import GmailMailer
from src.config import Settings

def test_send_email_mocked():
    settings = Settings(
        gmail_user="test@gmail.com",
        gmail_app_password="test_password",
        email_to="recv@example.com"
    )
    mailer = GmailMailer(settings)

    with patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        success = mailer.send(
            subject="【测试邮件】2026-09-23",
            html_content="<h1>测试内容</h1>"
        )
        assert success is True
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("test@gmail.com", "test_password")
        instance.sendmail.assert_called_once()

def test_mailer_missing_credentials():
    settings = Settings()
    mailer = GmailMailer(settings)
    with pytest.raises(ValueError, match="缺少 GMAIL_USER 或 GMAIL_APP_PASSWORD"):
        mailer.send(subject="Test", html_content="Content")
