"""
Simple Email Service for CodeFlowOps
Handles email verification and password reset emails
"""
import os
import smtplib
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    """Simple email service for sending verification codes"""
    
    def __init__(self):
        # Load SMTP configuration from environment
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@codeflowops.com')
        
        # For development, we'll just log the email instead of sending
        self.dev_mode = os.getenv('ENV', 'development') == 'development'
    
    async def send_verification_code(self, email: str, code: str) -> bool:
        """Send verification code to email"""
        try:
            if self.dev_mode or not self.smtp_username:
                # Development mode - just log the email
                logger.info(f"[DEV MODE] Email to {email}: Your verification code is {code}")
                return True
            
            # Create email message
            message = MIMEMultipart()
            message['From'] = self.from_email
            message['To'] = email
            message['Subject'] = "CodeFlowOps - Verification Code"
            
            # Email body
            body = f"""
            Hello,
            
            Your verification code for CodeFlowOps is: {code}
            
            This code will expire in 10 minutes.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            CodeFlowOps Team
            """
            
            message.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                text = message.as_string()
                server.sendmail(self.from_email, email, text)
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False
    
    async def send_password_reset_code(self, email: str, code: str) -> bool:
        """Send password reset code to email"""
        try:
            if self.dev_mode or not self.smtp_username:
                # Development mode - just log the email
                logger.info(f"[DEV MODE] Password reset email to {email}: Your reset code is {code}")
                return True
            
            # Create email message
            message = MIMEMultipart()
            message['From'] = self.from_email
            message['To'] = email
            message['Subject'] = "CodeFlowOps - Password Reset Code"
            
            # Email body
            body = f"""
            Hello,
            
            Your password reset code for CodeFlowOps is: {code}
            
            This code will expire in 24 hours.
            
            If you didn't request a password reset, please ignore this email.
            
            Best regards,
            CodeFlowOps Team
            """
            
            message.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                text = message.as_string()
                server.sendmail(self.from_email, email, text)
            
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
