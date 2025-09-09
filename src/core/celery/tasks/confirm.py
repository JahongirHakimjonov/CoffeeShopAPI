import asyncio
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from aiosmtplib import send
from celery import Task
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from pydantic import EmailStr

from core.celery.app import celery_app
from core.settings import settings, smtp_settings


def render_template(template_name: str, context: dict) -> str:
    """
    Render HTML template with Jinja2.
    """
    base = Path(__file__).resolve().parent.parent.parent.parent.parent
    templates_dir = base / "assets" / "templates"

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(**context)


@celery_app.task(  # type: ignore
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="send_confirm_task",
)
def send_confirm_task(self: Task, email: EmailStr, code: int) -> None:
    """
    Celery task to send confirmation email.
    Runs synchronously in Celery worker, but internally uses async SMTP send.
    """
    try:
        from_email = smtp_settings.sender_email
        smtp_host = smtp_settings.host
        smtp_port = smtp_settings.port
        smtp_user = smtp_settings.user
        smtp_password = smtp_settings.password

        if not from_email or not smtp_user or not smtp_password:
            raise ValueError("SMTP settings are missing in environment variables.")

        subject = "Activate Your Account"
        context = {
            "code": code,
            "current_year": datetime.now(UTC).year,
            "domain": settings.domain,
            "email": email,
        }

        # Render HTML with Jinja2 template
        html_content = render_template("confirm.html", context)
        text_content = f"Your confirmation code is {code}. This code will expire soon."

        # Prepare email
        message = MIMEMultipart("alternative")
        message["From"] = f"CoffeShop <{from_email}>"
        message["To"] = email
        message["Subject"] = subject
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        # Run async send inside sync Celery task
        asyncio.run(
            send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=True,
            )
        )

        logger.info(f"Confirmation email successfully sent to {email}")

    except Exception as e:
        logger.error(f"Failed to send confirmation email to {email}: {e}")
        raise
