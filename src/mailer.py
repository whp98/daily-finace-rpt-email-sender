import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import Settings

class GmailMailer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def send(self, subject: str, html_content: str) -> bool:
        if not self.settings.gmail_user or not self.settings.gmail_app_password:
            raise ValueError("缺少 GMAIL_USER 或 GMAIL_APP_PASSWORD 配置")
        if not self.settings.email_to:
            raise ValueError("缺少 EMAIL_TO 收件人配置")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Finance Daily Reporter <{self.settings.gmail_user}>"
        msg["To"] = self.settings.email_to

        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.settings.gmail_user, self.settings.gmail_app_password)
                server.sendmail(self.settings.gmail_user, [self.settings.email_to], msg.as_string())
            return True
        except Exception as e:
            print(f"[Mailer] 邮件发送失败: {e}")
            return False
