# tele_decode_bot.py
import telebot
import os
from decode_tool import decode_file, save_decoded, slash_dump_mode
import logging

# Setup logging
logging.basicConfig(
    filename="spyblade_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
TOKEN = "YOUR_BOT_TOKEN"  # Replace with your actual bot token
ALLOWED_USERS = [6244445306]  # List of allowed Telegram user IDs

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    welcome_text = (
        "🤖 *SlayerBot - Demon Decoder* 🤖\n\n"
        "Send me a `.py`, `.pyc`, or `.zip` file and I will:\n"
        "🔍 Detect: marshal, base64, XOR, zlib, pyc, zipapps\n"
        "🧪 Inject: a trap `.so` to catch native demons\n"
        "📤 Return: full decoded code + log if demon triggered\n\n"
        "*Commands:*\n"
        "`/last` - get last decoded file\n"
        "`/log` - get latest spyblade_log.txt\n"
        "`/slash` - fast extract mode (raw payloads)"
    )

    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['slash'])
def handle_slash(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    last_file = sorted([f for f in os.listdir("decoded") if f.endswith(".py")], reverse=True)
    if not last_file:
        bot.reply_to(message, "No decoded files available.")
        return

    base_path = os.path.join("decoded", last_file[0])
    results = slash_dump_mode(base_path)

    if not results:
        bot.reply_to(message, "No extractable base64 payloads found.")
        return

    bot.send_message(message.chat.id, f"Extracted {len(results)} payload(s):")
    for r in results:
        with open(r, 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f"Extracted: {r}")

@bot.message_handler(commands=['log'])
def send_log(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return
    try:
        with open("spyblade_log.txt", "rb") as log:
            bot.send_document(message.chat.id, log, caption="📝 Spyblade Log")
    except FileNotFoundError:
        bot.reply_to(message, "Log file not found.")

@bot.message_handler(commands=['last'])
def send_last(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    decoded = sorted([f for f in os.listdir("decoded") if f.endswith(".md")], reverse=True)
    if not decoded:
        bot.reply_to(message, "No analysis reports available.")
        return

    with open(os.path.join("decoded", decoded[0]), "rb") as f:
        bot.send_document(message.chat.id, f, caption="📊 Last Analysis Report")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        return

    file_name = message.document.file_name
    if not file_name.lower().endswith('.py'):
        bot.reply_to(message, "Please send only Python (.py) files for analysis.")
        return

    processing_msg = bot.reply_to(message, "🔍 Processing your file... This may take a moment.")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        safe_filename = f"input_{message.from_user.id}_{message.message_id}.py"
        with open(safe_filename, "wb") as f:
            f.write(downloaded)

        logging.info(f"Received file: {file_name} from user {message.from_user.id}")
        bot.edit_message_text("File received. Running analysis...", message.chat.id, processing_msg.message_id)

        decoded, emoji = decode_file(safe_filename)
        output_path = save_decoded(decoded)

        with open(output_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"{emoji} Analysis Report")

        try:
            with open("spyblade_log.txt", "rb") as log:
                bot.send_document(message.chat.id, log, caption="📝 Log")
        except FileNotFoundError:
            pass

        os.remove(safe_filename)

    except Exception as e:
        bot.reply_to(message, f"❌ Error processing file: {str(e)}")
        logging.error(f"Error processing file from user {message.from_user.id}: {str(e)}")

def main():
    if not os.path.exists("decoded"):
        os.makedirs("decoded")
    logging.info("SlayerBot is live.")
    print("SlayerBot is running...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
