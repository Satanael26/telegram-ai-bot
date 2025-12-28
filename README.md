🤖 Telegram AI Companion Bot – You’re not alone

This project is a personal AI companion for Telegram, created especially for people who feel alone and just need someone to talk to, anytime.

It’s not just about answers.
It’s about having presence, company, and support inside your pocket.

If this bot has helped you feel less alone, you can support its development here:

👉 https://ko-fi.com/sammy26

Your contribution helps keep this companion alive for others who need it 💙

⚙️ Requirements

Python 3.10+

Environment variables:

TELEGRAM_TOKEN: your bot token (required)

DONATION_URL: PayPal / Ko-fi link (optional)

ADMIN_IDS: comma-separated list of Telegram user IDs that will receive error alerts and can use admin commands. Example: "12345678,87654321"

LOG_LEVEL: log level (DEBUG, INFO, WARNING, ERROR). Default: INFO

LOG_FILE: log file name. Default: bot.log

SENTRY_DSN: Sentry DSN for remote error reporting (optional)

🛠 Installation

PowerShell (temporary):

python -m pip install -r requirements.txt
$env:TELEGRAM_TOKEN = "YOUR_TOKEN_HERE"
$env:DONATION_URL = "https://ko-fi.com/YOUR_USERNAME"  # optional
python .\bot.py

📌 Available Commands

/start – start the bot

/donar or /donate – show donation link

/help – show help (localized according to client language: es/en/ru)

⚠️ Notes

Keep your bot token private. Do not upload it to public repositories.

For production, consider using webhooks, logging, and a database for user and credit persistence.

Logging: the bot writes logs to console and to a rotating file (LOG_FILE). You can configure LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, and LOG_BACKUP_COUNT.

To receive error alerts via Sentry, configure SENTRY_DSN.
