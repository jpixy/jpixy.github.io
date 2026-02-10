#!/usr/bin/env python3
"""
Encrypt directory listings for protected sections during build.

This script:
1. Finds sections marked with `protected = true`
2. Encrypts the page list (titles and URLs)
3. Updates _index.md with encrypted data

Article content is encrypted separately by StatiCrypt after Zola build.

Usage:
    PROTECTED_PASSWORD=${{ secrets.ENCRYPT_PASSWORD }} python scripts/encrypt_on_build.py
"""

import os
import sys
import json
import hashlib
import base64
import re
from pathlib import Path

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Installing pycryptodome...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome"])
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from Crypto.Random import get_random_bytes


def sha256_hash(password: str) -> str:
    """Generate SHA256 hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()


def encrypt_aes_cryptojs(data: str, password: str) -> str:
    """Encrypt data compatible with CryptoJS.AES.decrypt."""
    salt = get_random_bytes(8)
    
    key_iv = b""
    prev = b""
    while len(key_iv) < 48:
        prev = hashlib.md5(prev + password.encode() + salt).digest()
        key_iv += prev
    
    key = key_iv[:32]
    iv = key_iv[32:48]
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    
    result = b"Salted__" + salt + encrypted
    return base64.b64encode(result).decode()


def is_section_protected(index_file: Path) -> bool:
    """Check if a section is marked as protected."""
    if not index_file.exists():
        return False
    
    content = index_file.read_text(encoding="utf-8")
    return bool(re.search(r'^\s*protected\s*=\s*true', content, re.MULTILINE))


def get_pages_from_section(section_path: Path) -> list:
    """Extract page info from markdown files."""
    pages = []
    
    for md_file in sorted(section_path.glob("*.md")):
        if md_file.name == "_index.md":
            continue
        
        content = md_file.read_text(encoding="utf-8")
        
        title_match = re.search(r'^title\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        title = title_match.group(1) if title_match else md_file.stem
        
        slug = md_file.stem
        section_name = section_path.name
        url = f"/articles/{section_name}/{slug}/"
        
        pages.append({"title": title, "url": url})
    
    return pages


def update_index_with_encryption(index_file: Path, password: str, password_hash: str, pages: list):
    """Update _index.md with encrypted page list."""
    content = index_file.read_text(encoding="utf-8")
    
    # Create encrypted pages data
    pages_json = json.dumps(pages, ensure_ascii=False)
    encrypted_pages = encrypt_aes_cryptojs(pages_json, password)
    
    # Remove old encrypted_pages and password_hash if exists
    content = re.sub(r'\nencrypted_pages\s*=\s*"[^"]*"', '', content)
    content = re.sub(r'\npassword_hash\s*=\s*"[^"]*"', '', content)
    
    # Add new fields after protected = true
    if 'protected = true' in content:
        content = content.replace(
            'protected = true',
            f'protected = true\npassword_hash = "{password_hash}"\nencrypted_pages = "{encrypted_pages}"'
        )
    
    index_file.write_text(content, encoding="utf-8")
    print(f"  [OK] Encrypted {len(pages)} page titles")


def main():
    # Get password from environment
    password = os.environ.get('PROTECTED_PASSWORD')
    if not password:
        print("WARNING: PROTECTED_PASSWORD not set, skipping directory encryption")
        print("Set PROTECTED_PASSWORD environment variable to enable encryption")
        sys.exit(0)  # Don't fail, just skip
    
    content_dir = Path(os.environ.get('CONTENT_DIR', 'content/articles'))
    
    if not content_dir.exists():
        print(f"ERROR: Content directory '{content_dir}' not found")
        sys.exit(1)
    
    password_hash = sha256_hash(password)
    
    print("=" * 60)
    print("Encrypting directory listings for protected sections...")
    print(f"Password hash: {password_hash[:16]}...")
    print("=" * 60)
    
    encrypted_count = 0
    
    # Find all protected sections
    for section_dir in sorted(content_dir.iterdir()):
        if not section_dir.is_dir():
            continue
        
        index_file = section_dir / "_index.md"
        
        if is_section_protected(index_file):
            print(f"\n📁 {section_dir.name}")
            
            pages = get_pages_from_section(section_dir)
            
            if pages:
                update_index_with_encryption(index_file, password, password_hash, pages)
                encrypted_count += 1
            else:
                print("  [SKIP] No articles found")
    
    print("\n" + "=" * 60)
    print(f"Done: {encrypted_count} directories encrypted")
    print("Article content will be encrypted by StatiCrypt after build")
    print("=" * 60)


if __name__ == "__main__":
    main()
