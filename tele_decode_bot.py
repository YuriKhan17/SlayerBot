# tele_decode_bot.py
import telebot
import os
from decode_tool import decode_file, save_decoded
import logging

# Logging config
logging.basicConfig(
    filename="spyblade_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Bot config
TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
ALLOWED_USERS = [TELE_ID]

bot = telebot.TeleBot(TOKEN)
last_decoded_path = None  # Global state for /last

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    welcome_text = (
        "🤖 *SlayerBot \\- Demon Decoder* 🤖\n\n"
        "Send me a `.py`, `.pyc`, or `.zip` file and I will:\n"
        "🔍 Detect: marshal, base64, XOR, zlib, pyc, zipapps\n"
        "🧪 Inject: a trap `.so` to catch native demons\n"
        "📤 Return: full decoded code \\+ log if demon triggered\n\n"
        "*Commands:*\n"
        "`/last` \\- get last decoded file\n"
        "`/log` \\- get latest spyblade\\_log\\.txt"
    )

    bot.reply_to(message, welcome_text, parse_mode="MarkdownV2")


@bot.message_handler(commands=['last'])
def send_last(message):
    global last_decoded_path
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    if last_decoded_path and os.path.exists(last_decoded_path):
        with open(last_decoded_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption="📄 Last Decoded File")
    else:
        bot.reply_to(message, "No file has been decoded yet.")

@bot.message_handler(commands=['log'])
def send_log(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    if os.path.exists("spyblade_log.txt"):
        with open("spyblade_log.txt", "rb") as f:
            bot.send_document(message.chat.id, f, caption="📝 Trap Log")
    else:
        bot.reply_to(message, "No trap log was found.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    global last_decoded_path

    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        logging.warning(f"Blocked user: {message.from_user.id}")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    filename = f"input_{message.chat.id}_{message.message_id}_{message.document.file_name}"
    
    # Save uploaded file
    with open(filename, "wb") as f:
        f.write(downloaded)

    # Feedback
    status = bot.reply_to(message, "🧠 Decoding the demon...")

    try:
        decoded, emoji = decode_file(filename)
        output_path = save_decoded(decoded)
        last_decoded_path = output_path

        # Send decoded output
        with open(output_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"{emoji} Decoded Output")

        # Send trap log if triggered
        if os.path.exists("spyblade_log.txt"):
            with open("spyblade_log.txt", "rb") as log:
                bot.send_document(message.chat.id, log, caption="🧿 Trap Log")

        # Clean temp
        os.remove(filename)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error decoding: {str(e)}")
        logging.error(f"Error decoding {filename}: {str(e)}")

def main():
    os.makedirs("decoded", exist_ok=True)
    print("🔥 SlayerBot is running...")
    logging.info("Bot started.")
    bot.polling(none_stop=True, timeout=10, long_polling_timeout=100)


if __name__ == "__main__":
    main()
