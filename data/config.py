from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot Token
ADMINS = env.list("ADMINS")  # adminlar ro'yxati


DB_USER = env.str("DB_USER")
DB_PASS = env.str("DB_PASS")
DB_NAME = env.str("DB_NAME")
DB_HOST = env.str("DB_HOST")

# SMTP Configuration
SMTP_HOST = env.str("SMTP_HOST", default="")
SMTP_PORT = env.int("SMTP_PORT", default=465)
SMTP_USER = env.str("SMTP_USER", default="")
SMTP_PASS = env.str("SMTP_PASS", default="")
SMTP_USE_SSL = env.bool("SMTP_USE_SSL", default=True)
SMTP_FROM = env.str("SMTP_FROM", default="")
SMTP_FROM_NAME = env.str("SMTP_FROM_NAME", default="Telegram Bot")

# AI & Gemini API Configuration
GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")


