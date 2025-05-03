# tele_decode_bot.py
import telebot
import os
import time
import logging
from decode_tool import decode_file, save_decoded, slash_dump_mode

API_TOKEN = 'TELEGRAM_TOKEN'
ALLOWED_USERS = [ALLOWED_USERS]  # Replace with your Telegram user ID

bot = telebot.TeleBot(API_TOKEN)
logging.basicConfig(level=logging.INFO)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    welcome_text = (
        "🤖 SlayerBot Activated!\n\n"
        "Send me an obfuscated Python file (.py, .pyc, or .zip)\n"
        "and I will decode it for you.\n\n"
        "Commands:\n"
        "/last - Get last decoded file\n"
        "/log - Get latest spyblade_log.txt\n"
        "/slash - Extract slash dumped payload (if present)"
    )
    bot.reply_to(message, welcome_text)  # no parse_mode here

@bot.message_handler(commands=['last'])
def send_last_decoded(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    try:
        latest = sorted([f for f in os.listdir('.') if f.startswith("decoded_")], reverse=True)[0]
        with open(latest, 'rb') as f:
            bot.send_document(message.chat.id, f)
    except IndexError:
        bot.reply_to(message, "No decoded files found.")

@bot.message_handler(commands=['log'])
def send_spyblade_log(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    if os.path.exists("spyblade_log.txt"):
        with open("spyblade_log.txt", 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.reply_to(message, "spyblade_log.txt not found.")

@bot.message_handler(commands=['slash'])
def handle_slash(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    if os.path.exists("decoded_last.py"):
        payload_path = slash_dump_mode("decoded_last.py")
        if payload_path and os.path.exists(payload_path):
            with open(payload_path, 'rb') as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.reply_to(message, "No base64 payload found.")
    else:
        bot.reply_to(message, "No last decoded file available.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    fname = f"temp_{int(time.time())}_{message.document.file_name}"
    with open(fname, 'wb') as f:
        f.write(downloaded_file)

    try:
        result = decode_file(fname)

        if isinstance(result, tuple):
            decoded_code, original_name = result
            final_path = save_decoded(decoded_code, original_name)
        else:
            final_path = save_decoded(result)

        with open(final_path, 'rb') as f:
            bot.send_document(message.chat.id, f)

        if os.path.exists("spyblade_log.txt"):
            with open("spyblade_log.txt", 'rb') as f:
                bot.send_document(message.chat.id, f)

    except Exception as e:
        bot.reply_to(message, f"Decoding failed: {e}")
    finally:
        if os.path.exists(fname):
            os.remove(fname)

if __name__ == "__main__":
    print("SlayerBot is running...")
    bot.infinity_polling()

