# 🔍 SlayerBot - Advanced Python Malware Analysis Toolkit

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

**SlayerBot** is an automated malware analysis tool designed to deobfuscate and analyze malicious Python scripts. It combines multi-layer decoding, behavioral analysis, and a **honeypot trap** to detect and log malicious activity.

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Layer Decoding** | Decodes `base64`, `marshal`, `zlib`, `XOR`, `eval/exec` chains, and embedded `.zip` files |
| **Behavioral Analysis** | AST-based detection of dangerous calls (`system`, `eval`, `ctypes`) |
| **Network Forensics** | Extracts URLs, IPs, and API keys from obfuscated payloads |
| **Honeypot Trap** | `Fake.so` logs malware interactions with native libraries |
| **Telegram Bot** | Secure remote analysis via encrypted Telegram API |
| **Markdown Reports** | Detailed analysis output with risk scoring |

---

## ⚙️ Installation

### Prerequisites
- Python 3.7+
- Linux/macOS (Windows untested)
- Telegram Bot Token ([@BotFather](https://t.me/botfather))

### Steps
```bash
git clone https://github.com/YuriKhan17/SlayerBot.git
cd SlayerBot

# Install dependencies
pip install -r requirements.txt

# Compile the honeypot trap
make clean && make

# Configure environment variables
echo "TELEGRAM_TOKEN=your_bot_token" > .env
echo "ALLOWED_USERS=YOUR_ID" >> .env  # Replace with your Telegram ID

# Run the bot
python tele_decode_bot.py
```

## 🛡️ Usage

### Telegram Bot Commands

| Command | Action |
|---------|--------|
| `/start` | Show bot introduction |
| `/help` | List available commands |
| `/log` | Download malware interaction logs |
| `/last` | Retrieve the latest analysis report |

### Sample Workflow
1. Send a suspicious `.py` file to your bot
2. Receive automated analysis:
   * Decoded source code
   * Extracted IOCs (IPs/URLs)
   * Behavioral flags
3. Check `spyblade_log.txt` for trap triggers

## 🏗️ Project Structure

```
SlayerBot/
├── tele_decode_bot.py        # Telegram bot interface
├── decode_tool.py            # Core deobfuscation engine
├── Fake.c                    # Honeypot trap (compiles to .so)
├── spyblade_log.txt          # Malware interaction logs
├── decoded/                  # Analysis reports
├── Makefile                  # Trap compilation
└── requirements.txt          # Python dependencies
```

## ⚠️ Security Considerations

1. **Isolate Execution**
   * Run in a **Docker container** or VM:
```bash
docker build -t slayerbot . && docker run -it slayerbot
```

2. **Token Protection**
   * Never hardcode credentials. Use `.env` + `python-dotenv`.
   
3. **Input Validation**
   * All user uploads are saved with sanitized filenames.

## 📜 License

MIT License. See LICENSE for details.

**Disclaimer**: Use only for **authorized security research**. The developers assume no liability for misuse.

## 📬 Contact

* **Author**: [Yuri]
* **Telegram**: ([@r4_cm](https://t.me/r4_cm)
