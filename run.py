# Точка входа: запускает сайт (Flask) и Telegram-бота.
# Сайт работает в отдельном потоке, бот (polling) — в основном.

import os
import sys
import threading

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

from db import init_db  # noqa: E402
from app import app as flask_app  # noqa: E402

PORT = int(os.environ.get('PORT', 3000))


def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT, use_reloader=False)


def main():
    init_db()

    token = os.environ.get('TELEGRAM_BOT_TOKEN')

    print(f"🌍 Сайт запущен: http://localhost:{PORT}")
    print(f"🛠  Панель модерации: http://localhost:{PORT}/admin.html")

    if token:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        from bot import build_bot

        bot_app = build_bot()
        print("🤖 Telegram-бот запущен")
        bot_app.run_polling()
    else:
        print("⚠️  TELEGRAM_BOT_TOKEN не задан в .env — бот не запущен (сайт при этом работает)")
        run_flask()


if __name__ == '__main__':
    main()
