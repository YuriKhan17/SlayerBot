# tele_decode_bot.py
import telebot
import os
from decode_tool import decode_file, save_decoded
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
    """Handle start and help commands"""
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        logging.warning(f"Unauthorized access attempt from user {message.from_user.id}")
        return
    
    welcome_text = (
        "🔍 *SlayerBot Malware Analyzer* 🔍\n\n"
        "Send me any Python file and I'll analyze it for malicious content.\n\n"
        "I can detect:\n"
        "- Encoding methods (base64, marshal, zlib)\n"
        "- Obfuscation techniques\n"
        "- Suspicious imports\n"
        "- Network connections\n"
        "- And more!\n\n"
        "Just send me a .py file to get started."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    """Handle document uploads"""
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "Access Denied.")
        logging.warning(f"Unauthorized access attempt from user {message.from_user.id}")
        return
    
    # Check if the file is a Python file
    file_name = message.document.file_name
    if not file_name.lower().endswith('.py'):
        bot.reply_to(message, "Please send only Python (.py) files for analysis.")
        return
    
    # Send a processing message
    processing_msg = bot.reply_to(message, "🔍 Processing your file... This may take a moment.")
    
    try:
        # Download the file
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # Create a safe filename
        safe_filename = f"input_{message.from_user.id}_{message.message_id}.py"
        
        # Save the file
        with open(safe_filename, "wb") as f:
            f.write(downloaded)
        
        # Log the file reception
        logging.info(f"Received file: {file_name} from user {message.from_user.id}")
        
        # Notify user
        bot.edit_message_text("File received. Running analysis...", 
                             message.chat.id, 
                             processing_msg.message_id)
        
        # Analyze the file
        decoded = decode_file(safe_filename)
        output_path = save_decoded(decoded)
        
        # Send the analysis back
        with open(output_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption="📊 Analysis Report")
        
        # Send log file if it exists
        try:
            with open("spyblade_log.txt", "rb") as log:
                bot.send_document(message.chat.id, log, caption="📝 Analysis Logs")
        except FileNotFoundError:
            pass
        
        # Clean up
        os.remove(safe_filename)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error processing file: {str(e)}")
        logging.error(f"Error processing file from user {message.from_user.id}: {str(e)}")

def main():
    """Main function to start the bot"""
    # Create necessary directories
    if not os.path.exists("decoded"):
        os.makedirs("decoded")
    
    # Start the bot
    logging.info("Starting SlayerBot...")
    print("SlayerBot is running...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
