# decode_tool.py
import os
import base64
import re
import binascii
import marshal
import zlib
import dis
import ast
import zipfile
from datetime import datetime
import logging

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
    """Clean unsafe chars for Markdown and truncate output."""
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

def extract_key_strings(content):
    def is_readable(s):
        return all(32 <= ord(c) <= 126 for c in s)

    # Extract potential strings
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
        # ZIP handling
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
        if encoding_types:
            for encoding in encoding_types:
                decoded_output += f"- {encoding}\n"
        else:
            decoded_output += "- No common encoding methods detected\n"

        strings = extract_key_strings(content)
        decoded_output += "\n## Key Strings Found\n"
        for section, values in strings.items():
            if values:
                decoded_output += f"\n### {section.capitalize()}:\n"
                for val in values:
                    decoded_output += f"- {val}\n"

        suspicious_imports = analyze_imports(content)
        decoded_output += "\n## Suspicious Import Analysis\n"
        if suspicious_imports:
            decoded_output += "The following potentially dangerous libraries were imported:\n"
            for imp in suspicious_imports:
                decoded_output += f"- {imp}\n"
        else:
            decoded_output += "- No commonly suspicious libraries detected\n"

        decoded_output += "\n## Decoding Attempts\n"

        if 'base64' in encoding_types:
            decoded_output += "\n### Base64 Decoding Attempt:\n"
            base64_match = re.findall(r'[\'"]([A-Za-z0-9+/=]{20,})[\'"]', content)
            for i, match in enumerate(base64_match[:3]):
                decoded = try_base64_decode(match)
                if decoded:
                    injected = inject_trap_to_code(decoded)
                    with open(f"decoded/base64_decoded_{i+1}.py", "w") as f:
                        f.write(injected)
                    decoded_output += f"```python\n{safe_snippet(injected)}\n```\n"

        if 'marshal' in encoding_types and binary_content:
            decoded_output += "\n### Marshal Decoding Attempt:\n"
            marshal_result = try_marshal_decode(binary_content)
            if marshal_result:
                with open("decoded/unmarshalled_content.py", "w") as f:
                    f.write(str(marshal_result))
                decoded_output += "```python\n# Successfully decoded marshal content\n```\n"
                decoded_output += "Marshal content saved to 'decoded/unmarshalled_content.py'\n"

        if 'zlib' in encoding_types and binary_content:
            decoded_output += "\n### Zlib Decompression Attempt:\n"
            zlib_result = try_zlib_decode(binary_content)
            if zlib_result:
                decoded_output += f"```python\n# Decompressed zlib content:\n{zlib_result[:500]}...\n```\n"

        if 'eval/exec' in encoding_types:
            decoded_output += "\n### Eval/Exec Obfuscation Analysis:\n"
            eval_patterns = re.findall(r'(eval|exec)\((.*?)\)', content, re.DOTALL)
            if eval_patterns:
                decoded_output += f"Found {len(eval_patterns)} instances of eval/exec obfuscation\n"
                decoded_output += "This is a common technique used to hide malicious code\n"

        decoded_output += "\n## Original Code (First 50 lines)\n```python\n"
        decoded_output += "\n".join(content.split("\n")[:50])
        if len(content.split("\n")) > 50:
            decoded_output += "\n# ... (truncated) ...\n"
        decoded_output += "```\n"

        decoded_output += "\n## Summary of Findings\n"
        risk_level = "Low"
        if suspicious_imports:
            risk_level = "Medium"
        if 'eval/exec' in encoding_types or ('marshal' in encoding_types and 'zlib' in encoding_types):
            risk_level = "High"

        decoded_output += f"- Risk Assessment: {risk_level}\n"
        decoded_output += f"- Encoding layers detected: {len(encoding_types)}\n"
        decoded_output += f"- Suspicious imports: {len(suspicious_imports)}\n"
        decoded_output += f"- External connections (URLs/IPs): {len(strings['urls']) + len(strings['ips'])}\n"

        decoded_output += "\n## Recommendations\n"
        decoded_output += "- Run the file in a sandboxed environment for dynamic analysis\n"
        decoded_output += "- Use a debugger to step through execution if further analysis is needed\n"
        if 'marshal' in encoding_types or 'zlib' in encoding_types:
            decoded_output += "- Use specialized tools to extract the marshal/zlib encoded payloads\n"

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

        logging.info("Analysis completed successfully")
        return decoded_output, emoji

    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        return f"# Error analyzing file\n\nAn error occurred: {str(e)}", "❌"

def save_decoded(content):
    if not os.path.exists("decoded"):
        os.makedirs("decoded")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"decoded/analysis_{timestamp}.md"
    with open(path, "w") as f:
        f.write(content)
    logging.info(f"Analysis saved to {path}")
    return path
