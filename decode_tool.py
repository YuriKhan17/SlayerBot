# SlayerBot Ultimate Decoder - Level 13+ Truth Seeker
import os
import base64
import re
import binascii
import marshal
import zlib
import dis
import ast
import zipfile
import logging
from datetime import datetime
from itertools import cycle
import struct

logging.basicConfig(
    filename="spyblade_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def detect_encoding(content):
    types = []
    if re.search(r'[A-Za-z0-9+/=]{20,}', content): types.append('base64')
    if re.search(r'(?:0x[0-9a-fA-F]{2}[, ]*){10,}', content): types.append('hex')
    if 'marshal.loads' in content: types.append('marshal')
    if 'zlib.decompress' in content: types.append('zlib')
    if re.search(r'eval\(|exec\(', content): types.append('eval/exec')
    if re.search(r'[\^].*?[\^]', content): types.append('possible XOR')
    return types


def safe_snippet(s, limit=500):
    return ''.join(c if 32 <= ord(c) <= 126 else '.' for c in s[:limit])


def extract_zip(path):
    out = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as z:
            z.extractall("decoded/")
            out = [os.path.join("decoded", f) for f in z.namelist() if f.endswith(".py")]
    return out


def inject_trap_to_code(code):
    trap = 'import ctypes\nctypes.CDLL("./Pyahmed.so")\n'
    return code if 'ctypes.CDLL' in code else trap + code


def try_base64_decode(data):
    try:
        return base64.b64decode(data.strip()).decode('utf-8', errors='replace')
    except: return None


def try_marshal_decode(data):
    try:
        match = re.search(rb'marshal\.loads\((.*?)\)', data, re.DOTALL)
        if match:
            mdata = eval(match.group(1))
            return marshal.loads(mdata)
    except: pass
    return None


def try_zlib_decode(data):
    try:
        match = re.search(rb'zlib\.decompress\((.*?)\)', data, re.DOTALL)
        if match:
            return zlib.decompress(eval(match.group(1))).decode('utf-8', errors='replace')
    except: pass
    return None


def xor_brute_force(data):
    try:
        for k in range(1, 256):
            plain = ''.join(chr(c ^ k) for c in data)
            if re.search(r'(import|exec|eval)', plain):
                return (k, plain)
    except: pass
    return None


def disassemble_codeobj(obj):
    try:
        return dis.code_info(obj) + "\n" + dis.Bytecode(obj).dis()
    except: return "[disassembly failed]"


def extract_key_strings(content):
    urls = re.findall(r'https?://[\w\-./?%&=]+', content)
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
    paths = re.findall(r'[\'/\"]([/\\][\w\-\.\\/]+)[\'/\"]', content)
    keys = re.findall(r'[\'/\"]([A-Za-z0-9_\-]{20,})[\'/\"]', content)
    return {'urls': urls, 'ips': ips, 'paths': paths, 'potential_keys': keys}


def analyze_imports(content):
    badlibs = ['socket','subprocess','ctypes','requests','os.system']
    found = []
    for lib in badlibs:
        if lib in content: found.append(lib)
    return found


def analyze_ast_behavior(code):
    flags = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id') and node.func.id in ['eval', 'exec']:
                    flags.append(f"Dynamic call: {node.func.id}()")
                if hasattr(node.func, 'attr') and node.func.attr in ['system', 'popen']:
                    flags.append(f"Dangerous call: {node.func.attr}()")
    except: pass
    return flags


def decode_file(filepath):
    try:
        if filepath.endswith(".zip"):
            out = extract_zip(filepath)
            return f"Extracted: {len(out)} files: {out}", "📦"

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        with open(filepath, 'rb') as f:
            btext = f.read()

        encs = detect_encoding(text)
        report = f"# SlayerBot Analysis for `{filepath}`\n"
        report += f"Detected Layers: {encs}\n"
        strings = extract_key_strings(text)
        for s, vals in strings.items():
            if vals:
                report += f"\n### {s.upper()}:\n" + '\n'.join(f"- {v}" for v in vals) + '\n'

        imports = analyze_imports(text)
        if imports:
            report += f"\n### Suspicious Imports:\n" + '\n'.join(f"- {imp}" for imp in imports)

        # Base64
        if 'base64' in encs:
            for match in re.findall(r'[\"\']([A-Za-z0-9+/=]{20,})[\"\']', text)[:3]:
                b = try_base64_decode(match)
                if b:
                    p = f"decoded/base64_{hash(match)}.py"
                    with open(p, 'w') as f: f.write(b)
                    report += f"\nDecoded base64 saved to `{p}`"
                    r, _ = decode_file(p)
                    report += f"\n--- Recursed ---\n{r}\n"

        # Marshal
        if 'marshal' in encs:
            obj = try_marshal_decode(btext)
            if obj:
                disasm = disassemble_codeobj(obj)
                with open("decoded/unmarshalled_dis.txt", 'w') as f: f.write(disasm)
                report += f"\nMarshal disassembly saved.\n```
{safe_snippet(disasm)}
```
"

        # Zlib
        if 'zlib' in encs:
            z = try_zlib_decode(btext)
            if z:
                zfile = "decoded/zlib_out.py"
                with open(zfile, 'w') as f: f.write(z)
                report += f"\nZlib decoded to `{zfile}`\n"
                r, _ = decode_file(zfile)
                report += f"\n--- Recursed ---\n{r}\n"

        # XOR
        if 'possible XOR' in encs:
            attempt = xor_brute_force(list(btext[:300]))
            if attempt:
                k, out = attempt
                report += f"\nXOR Key = {k}\n```\n{safe_snippet(out)}\n```"

        # Eval
        if 'eval/exec' in encs:
            report += "\nContains dynamic eval/exec call.\n"

        # AST analysis
        ast_flags = analyze_ast_behavior(text)
        if ast_flags:
            report += "\n### AST Behavior:\n" + '\n'.join(f"- {f}" for f in ast_flags)

        emoji = "📄"
        if 'marshal' in encs: emoji = "😈"
        elif 'zlib' in encs: emoji = "🧪"
        elif 'base64' in encs: emoji = "🔐"
        elif 'eval/exec' in encs: emoji = "🧠"

        return report, emoji

    except Exception as e:
        return f"# Error: {e}", "❌"


def save_decoded(content):
    os.makedirs("decoded", exist_ok=True)
    t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"decoded/analysis_{t}.md"
    with open(path, 'w') as f:
        f.write(content)
    return path


def slash_dump_mode(filepath):
    """Extracts and dumps all inner base64/marshal payloads without full analysis."""
    raw = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    b64s = re.findall(r'[\"\']([A-Za-z0-9+/=]{20,})[\"\']', content)
    for i, m in enumerate(b64s):
        out = try_base64_decode(m)
        if out:
            path = f"decoded/raw_b64_{i}.py"
            with open(path, 'w') as f:
                f.write(out)
            raw.append(path)
    return raw
