# decode_tool.py
import os
import base64
import re
import binascii
import marshal
import zlib
import dis
import ast
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    filename="spyblade_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def detect_encoding(content):
    """Detect potential encoding methods used in the file"""
    encoding_types = []
    
    # Check for base64 patterns
    if re.search(r'[A-Za-z0-9+/=]{20,}', content):
        encoding_types.append('base64')
    
    # Check for hex encoding
    if re.search(r'(?:0x[0-9a-fA-F]{2}[, ]*){10,}', content):
        encoding_types.append('hex')
    
    # Check for marshal usage
    if 'marshal.loads' in content:
        encoding_types.append('marshal')
    
    # Check for zlib compression
    if 'zlib.decompress' in content:
        encoding_types.append('zlib')

    # Check for eval/exec obfuscation
    if re.search(r'eval\(|exec\(', content):
        encoding_types.append('eval/exec')
        
    # Check for XOR patterns (common in obfuscated code)
    if re.search(r'[\^].*?[\^]', content) or re.search(r'for\s+.*?\s+in\s+.*?:\s+.*?\s*\^', content):
        encoding_types.append('possible XOR')
    
    return encoding_types

def try_base64_decode(data):
    """Attempt to decode base64 content"""
    try:
        decoded = base64.b64decode(data.strip())
        return decoded.decode('utf-8', errors='replace')
    except:
        logging.warning("Failed to decode using base64")
        return None

def try_marshal_decode(data):
    """Attempt to decode marshal content"""
    try:
        # Extract marshal bytes from the content
        match = re.search(rb'marshal\.loads\((.*?)\)', data, re.DOTALL)
        if match:
            marshalled_data = eval(match.group(1))
            unmarshalled = marshal.loads(marshalled_data)
            return unmarshalled
    except Exception as e:
        logging.warning(f"Failed to decode using marshal: {e}")
    return None

def try_zlib_decode(data):
    """Attempt to decode zlib compressed content"""
    try:
        # Look for zlib patterns
        match = re.search(rb'zlib\.decompress\((.*?)\)', data, re.DOTALL)
        if match:
            compressed_data = eval(match.group(1))
            decompressed = zlib.decompress(compressed_data)
            return decompressed.decode('utf-8', errors='replace')
    except Exception as e:
        logging.warning(f"Failed to decompress using zlib: {e}")
    return None

def extract_key_strings(content):
    """Extract potentially important strings from the code"""
    # Look for URLs
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', content)
    
    # Look for IP addresses
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
    
    # Look for file paths
    paths = re.findall(r'[\'"][\/\\][\w\-\.\/\\]+[\'"]', content)
    
    # Look for API keys and tokens (common patterns)
    api_keys = re.findall(r'[\'"][A-Za-z0-9_\-]{20,}[\'"]', content)
    
    return {
        'urls': urls,
        'ips': ips,
        'paths': paths,
        'potential_keys': api_keys
    }

def analyze_imports(content):
    """Analyze import statements to identify potentially malicious libraries"""
    suspicious_imports = []
    
    # Common libraries used in malicious code
    malicious_libraries = [
        'socket', 'subprocess', 'os.system', 'shutil', 'ctypes',
        'winreg', 'requests', 'pyautogui', 'pynput', 'pyHook',
        'pywin32', 'win32api', 'win32com', 'win32crypt',
        'urllib', 'ftplib', 'paramiko'
    ]
    
    # Extract import statements
    imports = re.findall(r'(?:from|import)\s+([^\s;]+)', content)
    
    for lib in malicious_libraries:
        for imp in imports:
            if lib in imp:
                suspicious_imports.append(lib)
                break
    
    return suspicious_imports

def decode_file(filepath):
    """Main function to decode and analyze the file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        binary_content = None
        with open(filepath, 'rb') as f:
            binary_content = f.read()
        
        logging.info(f"Processing file: {filepath}")
        
        # Start building the analysis report
        decoded_output = f"# Malware Analysis Report for {filepath}\n"
        decoded_output += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Detect encoding types
        encoding_types = detect_encoding(content)
        decoded_output += "## Detected Encoding Methods\n"
        if encoding_types:
            for encoding in encoding_types:
                decoded_output += f"- {encoding}\n"
        else:
            decoded_output += "- No common encoding methods detected\n"
        
        # Extract important strings
        strings = extract_key_strings(content)
        decoded_output += "\n## Key Strings Found\n"
        
        if strings['urls']:
            decoded_output += "\n### URLs:\n"
            for url in strings['urls']:
                decoded_output += f"- {url}\n"
        
        if strings['ips']:
            decoded_output += "\n### IP Addresses:\n"
            for ip in strings['ips']:
                decoded_output += f"- {ip}\n"
        
        if strings['paths']:
            decoded_output += "\n### File Paths:\n"
            for path in strings['paths']:
                decoded_output += f"- {path}\n"
        
        if strings['potential_keys']:
            decoded_output += "\n### Potential API Keys/Tokens:\n"
            for key in strings['potential_keys']:
                decoded_output += f"- {key}\n"
        
        # Analyze imports
        suspicious_imports = analyze_imports(content)
        decoded_output += "\n## Suspicious Import Analysis\n"
        if suspicious_imports:
            decoded_output += "The following potentially dangerous libraries were imported:\n"
            for imp in suspicious_imports:
                decoded_output += f"- {imp}\n"
        else:
            decoded_output += "- No commonly suspicious libraries detected\n"
        
        # Attempt to decode the content if encoded
        decoded_output += "\n## Decoding Attempts\n"
        
        # Try base64 decoding
        if 'base64' in encoding_types:
            decoded_output += "\n### Base64 Decoding Attempt:\n"
            base64_match = re.findall(r'[\'"]([A-Za-z0-9+/=]{20,})[\'"]', content)
            if base64_match:
                for i, match in enumerate(base64_match[:3]):  # Limit to first 3 matches
                    decoded = try_base64_decode(match)
                    if decoded:
                        decoded_output += f"```python\n# Decoded base64 string {i+1}:\n{decoded[:500]}...\n```\n"
        
        # Try to find and decode marshal content
        if 'marshal' in encoding_types and binary_content:
            decoded_output += "\n### Marshal Decoding Attempt:\n"
            marshal_result = try_marshal_decode(binary_content)
            if marshal_result:
                decoded_output += "```python\n# Successfully decoded marshal content\n```\n"
                # Save the unmarshalled content to a separate file
                with open("decoded/unmarshalled_content.py", "w") as f:
                    f.write(str(marshal_result))
                decoded_output += "Marshal content saved to 'decoded/unmarshalled_content.py'\n"
        
        # Try to find and decode zlib content
        if 'zlib' in encoding_types and binary_content:
            decoded_output += "\n### Zlib Decompression Attempt:\n"
            zlib_result = try_zlib_decode(binary_content)
            if zlib_result:
                decoded_output += f"```python\n# Decompressed zlib content:\n{zlib_result[:500]}...\n```\n"
        
        # Check for eval/exec obfuscation
        if 'eval/exec' in encoding_types:
            decoded_output += "\n### Eval/Exec Obfuscation Analysis:\n"
            eval_patterns = re.findall(r'(eval|exec)\((.*?)\)', content, re.DOTALL)
            if eval_patterns:
                decoded_output += f"Found {len(eval_patterns)} instances of eval/exec obfuscation\n"
                decoded_output += "This is a common technique used to hide malicious code\n"
        
        # Original code section
        decoded_output += "\n## Original Code (First 50 lines)\n```python\n"
        decoded_output += "\n".join(content.split("\n")[:50])
        if len(content.split("\n")) > 50:
            decoded_output += "\n# ... (truncated) ...\n"
        decoded_output += "```\n"
        
        # Summary of findings
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
        
        # Recommendations
        decoded_output += "\n## Recommendations\n"
        decoded_output += "- Run the file in a sandboxed environment for dynamic analysis\n"
        decoded_output += "- Use a debugger to step through execution if further analysis is needed\n"
        if 'marshal' in encoding_types or 'zlib' in encoding_types:
            decoded_output += "- Use specialized tools to extract the marshal/zlib encoded payloads\n"
        
        logging.info("Analysis completed successfully")
        return decoded_output
    
    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        return f"# Error analyzing file\n\nAn error occurred: {str(e)}"

def save_decoded(content):
    """Save the decoded content to a file"""
    # Make sure decoded directory exists
    if not os.path.exists("decoded"):
        os.makedirs("decoded")
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"decoded/analysis_{timestamp}.md"
    
    with open(path, "w") as f:
        f.write(content)
    
    logging.info(f"Analysis saved to {path}")
    return path


