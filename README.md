# SlayerBot - Python Malware Analysis Tool

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)

SlayerBot is an automated Telegram bot for analyzing obfuscated Python malware. It decodes various obfuscation techniques, analyzes suspicious behavior, and provides detailed reports for security research.

## 🔍 Features

- **Automated Multi-layer Deobfuscation**: Handles base64, marshal, zlib, XOR, eval/exec chains
- **Suspicious Import Analysis**: Identifies potentially malicious libraries and functions
- **Network Indicators Extraction**: Automatically extracts URLs, IPs, and API keys
- **Telegram Bot Interface**: Send malware samples, receive analysis reports
- **Honeypot Functionality**: Includes a trap `.so` file to log and analyze malware behavior
- **Detailed Reports**: Comprehensive Markdown reports with risk assessment

## 📋 Project Structure

```
SlayerBot/
├── decode_tool.py              🔍 Full decoder engine (XOR, marshal, .pyc, base64, zip, etc.)
├── tele_decode_bot.py         🤖 Telegram bot interface
├── FakePyahmed_v3.c           🪤 Trap .so to log and analyze demons
├── Makefile                   🛠 Auto compile trap
├── spyblade_log.txt           📓 Created when demon triggers the trap
├── decoded/                   📁 All timestamped decoded outputs
├── logs/                      📁 Telegram logs and outputs
├── requirements.txt           📦 Python packages
└── README.md                  📘 GitHub doc
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/YuriKhan17/SlayerBot.git
cd SlayerBot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Compile the trap `.so` file:
```bash
make
```

4. Configure your Telegram bot:
   - Create a bot with [@BotFather](https://t.me/botfather) on Telegram
   - Replace `YOUR_BOT_TOKEN` in `tele_decode_bot.py` with your actual token
   - Set your Telegram user ID in the `ALLOWED_USERS` list

5. Run the bot:
```bash
python tele_decode_bot.py
```

## 📊 Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to verify the bot is working
3. Upload any Python file containing suspected malware
4. The bot will analyze the file and return:
   - A detailed markdown report of findings
   - Log files if any suspicious activity was detected

## 🛡️ Security Notes

- **⚠️ Always handle malware with caution**
- Run this tool in a safe, isolated environment
- The trap `.so` file should be handled carefully as it's designed to attract malicious code
- Only allow trusted users access to your bot (set their user IDs in the allowed users list)

## 🧪 Advanced Usage

### Trap Mechanism

The `FakePyahmed_v3.c` file creates a shared object that mimics common tools used by malware. When malicious code attempts to use this library, it logs the interaction to `spyblade_log.txt` for analysis.

To build the trap:
```bash
make clean
make
```

### Customizing Decoders

You can extend the decoders in `decode_tool.py` to handle additional obfuscation techniques by implementing new detection and decoding functions.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

- Your Name - [your.email@example.com](mailto:your.email@example.com)
- Project Link: [https://github.com/YuriKhan17/SlayerBot](https://github.com/YuriKhan17/SlayerBot)

## 🙏 Acknowledgments

- [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram API wrapper
- All security researchers sharing knowledge on malware obfuscation techniques

---

⚠️ **Disclaimer**: This tool is for educational and research purposes only. Always use responsibly and legally.
