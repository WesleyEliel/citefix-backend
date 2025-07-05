from typing import List

from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from app.core.configs import settings


class EmailService:
    def __init__(self):
        print({
            "MAIL_USERNAME": settings.EMAIL_USERNAME,
            "MAIL_PASSWORD": settings.EMAIL_PASSWORD,
            "MAIL_FROM": settings.EMAIL_FROM,
            "MAIL_PORT": settings.EMAIL_PORT,
            "MAIL_SERVER": settings.EMAIL_SERVER,
            "MAIL_FROM_NAME": settings.EMAIL_FROM_NAME,
        })
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.EMAIL_USERNAME,
            MAIL_PASSWORD=settings.EMAIL_PASSWORD,
            MAIL_FROM=settings.EMAIL_FROM,
            MAIL_PORT=settings.EMAIL_PORT,
            MAIL_SERVER=settings.EMAIL_SERVER,
            MAIL_FROM_NAME=settings.EMAIL_FROM_NAME,
            # MAIL_STARTTLS=True,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER="./app/templates/v1/emails"
        )

    async def send_email_async(self, subject: str, recipients: List[EmailStr], template: str, context: dict):
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=context,
            subtype="html"
        )
        fm = FastMail(self.conf)
        await fm.send_message(message, template_name=template)

    def send_email_background(
            self,
            background_tasks: BackgroundTasks,
            subject: str,
            recipients: List[EmailStr],
            template: str,
            context: dict
    ):
        background_tasks.add_task(
            self.send_email_async,
            subject,
            recipients,
            template,
            context
        )


def get_email_service() -> EmailService:
    return EmailService()
