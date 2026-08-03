import os

TELEGRAM_TOKEN = os.environ.get("8581773614:AAEQu20iY-MjQ9HhS6xBamhZgx3r4nnpl2E")
DATABASE_URL = os.environ.get("postgres://avnadmin:AVNS_xePgM_KGoKWdYCRItQr@pg-38383ef6-kf677.e.aivencloud.com:23673/defaultdb?sslmode=require")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в переменных окружения!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не найден в переменных окружения!")
