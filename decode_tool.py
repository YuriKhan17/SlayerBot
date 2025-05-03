# decode_tool.py
import os
import base64
import re
import binascii
import marshal
import zlib
import dis
import ast
import time
import zipfile
from datetime import datetime
import logging
from itertools import cycle

# Set up logging
logging.basicConfig(
    filename="spyblade_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def detect_encoding(content):
    encoding_types = []
    if re.search(r'[A-Za-z0-9+/=]{20,}', content):
        encoding_types.append('base64')
    if re.search(r'(?:0x[0-9a-fA-F]{2}[, ]*){10,}', content):
        encoding_types.append('hex')
    if 'marshal.loads' in content:
        encoding_types.append('marshal')
    if 'zlib.decompress' in content:
        encoding_types.append('zlib')
    if re.search(r'eval\(|exec\(', content):
        encoding_types.append('eval/exec')
    if re.search(r'[\^].*?[\^]', content) or re.search(r'for\s+.*?\s+in\s+.*?:\s+.*?\s*\^', content):
        encoding_types.append('possible XOR')
    return encoding_types

def safe_snippet(s, limit=500):
    return ''.join(c if 32 <= ord(c) <= 126 else '.' for c in s[:limit])

def extract_zip(zip_path):
    extracted = []
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("decoded/")
            for f in z.namelist():
                if f.endswith(".py"):
                    extracted.append(os.path.join("decoded", f))
    return extracted

def inject_trap_to_code(code):
    trap_code = 'import ctypes\nctypes.CDLL("./Pyahmed.so")\n'
    if 'ctypes.CDLL' not in code:
        return trap_code + code
    return code

def try_base64_decode(data):
    try:
        decoded = base64.b64decode(data.strip())
        return decoded.decode('utf-8', errors='replace')
    except:
        logging.warning("Failed to decode using base64")
        return None

def try_marshal_decode(data):
    try:
        match = re.search(rb'marshal\.loads\((.*?)\)', data, re.DOTALL)
        if match:
            marshalled_data = eval(match.group(1))
            unmarshalled = marshal.loads(marshalled_data)
            return unmarshalled
    except Exception as e:
        logging.warning(f"Failed to decode using marshal: {e}")
    return None

def try_zlib_decode(data):
    try:
        match = re.search(rb'zlib\.decompress\((.*?)\)', data, re.DOTALL)
        if match:
            compressed_data = eval(match.group(1))
            decompressed = zlib.decompress(compressed_data)
            return decompressed.decode('utf-8', errors='replace')
    except Exception as e:
        logging.warning(f"Failed to decompress using zlib: {e}")
    return None

def xor_brute_force(data):
    results = []
    try:
        for key in range(1, 256):
            decoded = ''.join(chr(c ^ key) for c in data)
            if re.search(r'(import|def|exec|eval)', decoded):
                results.append((key, decoded))
                break
    except Exception as e:
        logging.warning(f"XOR brute failed: {e}")
    return results

def extract_key_strings(content):
    def is_readable(s):
        return all(32 <= ord(c) <= 126 for c in s)

    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', content)
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
    raw_paths = re.findall(r'[\'"]([\/\\][\w\-\.\/\\]+)[\'"]', content)
    paths = [p for p in raw_paths if is_readable(p)]
    raw_keys = re.findall(r'[\'"]([A-Za-z0-9_\-]{20,})[\'"]', content)
    potential_keys = [k for k in raw_keys if is_readable(k)]

    return {
        'urls': urls,
        'ips': ips,
        'paths': paths,
        'potential_keys': potential_keys
    }

def analyze_imports(content):
    suspicious_imports = []
    malicious_libraries = [
        'socket', 'subprocess', 'os.system', 'shutil', 'ctypes',
        'winreg', 'requests', 'pyautogui', 'pynput', 'pyHook',
        'pywin32', 'win32api', 'win32com', 'win32crypt',
        'urllib', 'ftplib', 'paramiko'
    ]
    imports = re.findall(r'(?:from|import)\s+([^\s;]+)', content)
    for lib in malicious_libraries:
        for imp in imports:
            if lib in imp:
                suspicious_imports.append(lib)
                break
    return suspicious_imports

def decode_file(filepath):
    try:
        if filepath.endswith(".zip"):
            extracted = extract_zip(filepath)
            decoded_output = f"## ZIP Extraction\nExtracted {len(extracted)} file(s):\n"
            for ex in extracted:
                decoded_output += f"- {ex}\n"
                decode_file(ex)
            return decoded_output, "📦"

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        with open(filepath, 'rb') as f:
            binary_content = f.read()

        logging.info(f"Processing file: {filepath}")

        decoded_output = f"# Malware Analysis Report for {filepath}\n"
        decoded_output += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        encoding_types = detect_encoding(content)
        decoded_output += "## Detected Encoding Methods\n"
        decoded_output += "\n".join(f"- {e}" for e in encoding_types) or "- None\n"

        strings = extract_key_strings(content)
        decoded_output += "\n## Key Strings Found\n"
        for section, values in strings.items():
            if values:
                decoded_output += f"\n### {section.capitalize()}:\n"
                for val in values:
                    decoded_output += f"- {val}\n"

        suspicious_imports = analyze_imports(content)
        decoded_output += "\n## Suspicious Import Analysis\n"
        decoded_output += "\n".join(f"- {imp}" for imp in suspicious_imports) or "- None\n"

        decoded_output += "\n## Decoding Attempts\n"

        # Base64 decoding
        if 'base64' in encoding_types:
            decoded_output += "\n### Base64 Decoding Attempt:\n"
            base64_match = re.findall(r'[\'"]([A-Za-z0-9+/=]{20,})[\'"]', content)
            for i, match in enumerate(base64_match[:3]):
                decoded = try_base64_decode(match)
                if decoded:
                    injected = inject_trap_to_code(decoded)
                    temp_path = f"decoded/base64_decoded_{i+1}.py"
                    with open(temp_path, "w") as f:
                        f.write(injected)
                    decoded_output += f"```python\n{safe_snippet(injected)}\n```\n"
                    try:
                        recursive_output, _ = decode_file(temp_path)
                        decoded_output += f"\n--- Recursive Layer from base64_decoded_{i+1}.py ---\n{recursive_output}\n"
                    except Exception as e:
                        logging.warning(f"Recursive decode failed (base64): {e}")

        # Marshal decoding
        if 'marshal' in encoding_types:
            decoded_output += "\n### Marshal Decoding Attempt:\n"
            result = try_marshal_decode(binary_content)
            if result:
                temp_path = "decoded/unmarshalled_content.py"
                with open(temp_path, "w") as f:
                    f.write(str(result))
                decoded_output += f"Unmarshalled and saved to `{temp_path}`\n"
                try:
                    recursive_output, _ = decode_file(temp_path)
                    decoded_output += f"\n--- Recursive Layer from unmarshalled_content.py ---\n{recursive_output}\n"
                except Exception as e:
                    logging.warning(f"Recursive decode failed (marshal): {e}")

        # Zlib decoding
        if 'zlib' in encoding_types:
            decoded_output += "\n### Zlib Decompression Attempt:\n"
            result = try_zlib_decode(binary_content)
            if result:
                temp_path = "decoded/zlib_decompressed.py"
                with open(temp_path, "w") as f:
                    f.write(result)
                decoded_output += f"Zlib decoded and saved to `{temp_path}`\n"
                try:
                    recursive_output, _ = decode_file(temp_path)
                    decoded_output += f"\n--- Recursive Layer from zlib_decompressed.py ---\n{recursive_output}\n"
                except Exception as e:
                    logging.warning(f"Recursive decode failed (zlib): {e}")

        # XOR brute force
        if 'possible XOR' in encoding_types:
            decoded_output += "\n### XOR Brute-Force Attempt:\n"
            xor_hits = xor_brute_force(list(binary_content[:400]))
            for key, result in xor_hits:
                decoded_output += f"Key: {key}\n```python\n{safe_snippet(result)}\n```\n"

        if 'eval/exec' in encoding_types:
            decoded_output += "\n### Eval/Exec Obfuscation Analysis:\n"
            patterns = re.findall(r'(eval|exec)\((.*?)\)', content, re.DOTALL)
            decoded_output += f"Found {len(patterns)} instance(s)\n"

        decoded_output += "\n## Original Code (First 50 lines)\n```python\n"
        decoded_output += "\n".join(content.splitlines()[:50]) + "\n```\n"

        # AI-style summary
        decoded_output += "\n## 🤖 AI-Style Summary\n"
        if 'marshal' in encoding_types and 'zlib' in encoding_types:
            decoded_output += "- Likely multi-layer packing: zlib > marshal > exec\n"
        if 'eval/exec' in encoding_types:
            decoded_output += "- Obfuscated logic hiding real payload\n"
        if 'base64' in encoding_types:
            decoded_output += "- Likely outer encoding of hidden payload\n"
        if suspicious_imports:
            decoded_output += "- Detected potential malware behavior (API abuse, system control)\n"
        if not encoding_types:
            decoded_output += "- Likely clean or static file\n"

        risk = "Low"
        if suspicious_imports:
            risk = "Medium"
        if 'eval/exec' in encoding_types or ('marshal' in encoding_types and 'zlib' in encoding_types):
            risk = "High"

        emoji = "📄"
        if 'marshal' in encoding_types:
            emoji = "😈"
        elif 'zlib' in encoding_types:
            emoji = "🧪"
        elif 'base64' in encoding_types:
            emoji = "🔐"
        elif filepath.endswith('.zip'):
            emoji = "📦"
        elif 'eval/exec' in encoding_types:
            emoji = "🧠"

        decoded_output += f"\n## Summary of Findings\n- Risk: {risk}\n"
        logging.info("Analysis completed")
        return decoded_output, emoji

    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        return f"# Error: {str(e)}", "❌"

def save_decoded(decoded_code, original_name="decoded_last.py"):
    # generate filename if not provided
    if not original_name.endswith(".py"):
        original_name += ".py"
    safe_name = f"decoded_{int(time.time())}_{original_name}"
    with open(safe_name, 'w', encoding='utf-8') as f:
        f.write(decoded_code)
    with open("decoded_last.py", 'w', encoding='utf-8') as f:
        f.write(decoded_code)
    return safe_name

def slash_dump_mode(filepath):
    outputs = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        with open(filepath, 'rb') as f:
            binary = f.read()
    except Exception as e:
        return f"[!] Error reading file: {e}"

    if 'marshal.loads' in content:
        try:
            match = re.search(rb'marshal\.loads\((.*?)\)', binary, re.DOTALL)
            if match:
                marshalled_data = eval(match.group(1))
                code = marshal.loads(marshalled_data)
                outputs.append(dis.code_info(code))
                outputs.append(dis.Bytecode(code).dis())
        except Exception as e:
            outputs.append(f"[!] Marshal decode failed: {e}")

    if 'base64' in content:
        matches = re.findall(r'[\'"]([A-Za-z0-9+/=]{20,})[\'"]', content)
        for i, match in enumerate(matches[:3]):
            try:
                decoded = base64.b64decode(match).decode('utf-8', errors='replace')
                outputs.append(f"[Base64 #{i+1}]\n{decoded}")
            except:
                continue

    if 'zlib.decompress' in content:
        try:
            match = re.search(rb'zlib\.decompress\((.*?)\)', binary, re.DOTALL)
            if match:
                compressed_data = eval(match.group(1))
                decompressed = zlib.decompress(compressed_data)
                outputs.append(f"[Zlib]\n{decompressed.decode('utf-8', errors='replace')}")
        except Exception as e:
            outputs.append(f"[!] Zlib decompress failed: {e}")

    if not outputs:
        return "[!] No recognizable payloads found."

    return "\n\n".join(str(o) for o in outputs)
