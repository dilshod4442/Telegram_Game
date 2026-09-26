import logging
from email.message import EmailMessage
from data import config

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Проверяет, заполнены ли настройки SMTP в конфигурации."""
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASS)


async def send_verification_email(to_email: str, code: str, user_name: str = "Пользователь") -> tuple[bool, str]:
    """
    Отправляет 6-значный код подтверждения на указанную почту.
    
    Возвращает:
        (True, "OK") - если письмо успешно отправлено
        (False, "NOT_CONFIGURED") - если SMTP не настроен в .env
        (False, error_details) - если произошла ошибка отправки
    """
    if not is_smtp_configured():
        logger.warning(
            f"SMTP не настроен! Письмо для {to_email} с кодом {code} не может быть отправлено через почтовый сервер."
        )
        return False, "NOT_CONFIGURED"

    try:
        import aiosmtplib

        msg = EmailMessage()
        from_display = config.SMTP_FROM_NAME or "Telegram Bot"
        from_email = config.SMTP_FROM or config.SMTP_USER
        msg["From"] = f"{from_display} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = f"🔐 Код подтверждения: {code}"

        plain_text = (
            f"Здравствуйте, {user_name}!\n\n"
            f"Ваш код для подтверждения регистрации в Telegram-боте: {code}\n"
            f"Код действителен в течение 10 минут.\n\n"
            f"Если вы не запрашивали данный код, просто проигнорируйте это сообщение."
        )

        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Код подтверждения</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #f4f6f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #333333;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 540px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 30px 25px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px;">🔐 Подтверждение регистрации</h1>
      </td>
    </tr>
    <tr>
      <td style="padding: 30px 25px;">
        <p style="font-size: 16px; line-height: 1.5; margin: 0 0 16px;">Здравствуйте, <strong>{user_name}</strong>!</p>
        <p style="font-size: 15px; line-height: 1.5; color: #4b5563; margin: 0 0 24px;">
          Вы указали данный адрес при регистрации в нашем Telegram-боте. Для завершения верификации введите следующий проверочный код:
        </p>
        
        <div style="background-color: #f0f7ff; border: 2px dashed #3b82f6; border-radius: 10px; padding: 20px; text-align: center; margin: 25px 0;">
          <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: 'Courier New', monospace;">{code}</span>
        </div>

        <p style="font-size: 14px; color: #6b7280; line-height: 1.5; margin: 0 0 10px; text-align: center;">
          ⏱ Код действителен в течение <strong>10 минут</strong>.
        </p>
        <p style="font-size: 13px; color: #9ca3af; line-height: 1.4; margin: 20px 0 0; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 15px;">
          Если вы не отправляли запрос на регистрацию в боте, просто проигнорируйте это письмо.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""

        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype="html")

        # Настройки SSL/TLS в зависимости от порта
        use_tls = config.SMTP_USE_SSL and config.SMTP_PORT == 465
        start_tls = config.SMTP_PORT == 587 or (not config.SMTP_USE_SSL and config.SMTP_PORT != 465)

        await aiosmtplib.send(
            msg,
            hostname=config.SMTP_HOST,
            port=config.SMTP_PORT,
            username=config.SMTP_USER,
            password=config.SMTP_PASS,
            use_tls=use_tls,
            start_tls=start_tls,
            timeout=10.0,
        )
        logger.info(f"Verification code successfully sent to {to_email}")
        return True, "OK"

    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}", exc_info=True)
        return False, str(exc)
