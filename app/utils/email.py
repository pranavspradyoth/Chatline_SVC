"""
CampusEats — Email utilities
"""
from flask import current_app, render_template_string
from flask_mail import Message
from .. import mail


RESET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Reset your CampusEats password</title>
</head>
<body style="margin:0;padding:0;background:#F0F7FF;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F7FF;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
          style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(43,127,224,.10);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a5fb7,#2B7FE0);padding:32px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-.02em;">
                🍽️ Campus<strong>Eats</strong>
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 24px;">
              <h2 style="margin:0 0 12px;color:#0F172A;font-size:20px;font-weight:700;">
                Reset your password
              </h2>
              <p style="margin:0 0 24px;color:#475569;font-size:15px;line-height:1.6;">
                Hi there! We received a request to reset the password for your CampusEats account
                associated with <strong style="color:#0F172A;">{{ email }}</strong>.
              </p>
              <p style="margin:0 0 28px;color:#475569;font-size:15px;line-height:1.6;">
                Click the button below to set a new password. This link will expire in
                <strong style="color:#0F172A;">1 hour</strong>.
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <a href="{{ reset_url }}"
                      style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#2B7FE0,#1a5fb7);
                             color:#ffffff;text-decoration:none;border-radius:10px;font-size:15px;
                             font-weight:600;letter-spacing:.01em;">
                      Reset my password
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Fallback link -->
          <tr>
            <td style="padding:0 40px 28px;">
              <p style="margin:0;font-size:12px;color:#94A3B8;line-height:1.6;">
                If the button doesn't work, paste this link into your browser:<br/>
                <a href="{{ reset_url }}" style="color:#2B7FE0;word-break:break-all;">{{ reset_url }}</a>
              </p>
            </td>
          </tr>

          <!-- Divider + security note -->
          <tr>
            <td style="padding:0 40px 32px;border-top:1px solid #E2E8F0;">
              <p style="margin:24px 0 0;font-size:12px;color:#94A3B8;line-height:1.6;">
                If you didn't request a password reset, you can safely ignore this email.
                Your password will not change.<br/><br/>
                — The CampusEats Team
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


def send_password_reset_email(user_email: str, reset_url: str) -> None:
    """Send a password-reset email to *user_email*."""
    html_body = render_template_string(
        RESET_EMAIL_TEMPLATE,
        email=user_email,
        reset_url=reset_url
    )
    msg = Message(
        subject="Reset your CampusEats password",
        recipients=[user_email],
        html=html_body,
        # Plain-text fallback
        body=(
            f"Reset your CampusEats password by visiting:\n{reset_url}\n\n"
            "This link expires in 1 hour. If you didn't request this, ignore this email."
        )
    )
    mail.send(msg)