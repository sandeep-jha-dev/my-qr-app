#!/usr/bin/env python3
"""
PDF to Link Converter
Convert any PDF file to a shareable link using transfer.sh, anonfiles, or 0x0.st.
Works as both a CLI tool and an importable module.
"""

import sys
import os
import requests
import argparse
import time
from pathlib import Path


def upload_pdf_to_host(file_path: str, retries: int = 3, base_delay: float = 1.0) -> str:
    """
    Upload a PDF file to public hosts and return a shareable link.
    
    Tries in order: transfer.sh (PUT) -> anonfiles (POST) -> 0x0.st (POST)
    Each host gets up to `retries` attempts with exponential backoff.
    
    Args:
        file_path: Path to the PDF file to upload.
        retries: Number of retry attempts per host (default 3).
        base_delay: Initial delay between retries in seconds (default 1.0).
        
    Returns:
        A shareable link to the uploaded PDF.
        
    Raises:
        FileNotFoundError: If file_path does not exist.
        RuntimeError: If all upload attempts fail.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.suffix.lower() == ".pdf":
        print(f"Warning: File {file_path.name} is not a .pdf file.")
    
    file_bytes = file_path.read_bytes()
    filename = file_path.name
    
    print(f"Uploading {filename} ({len(file_bytes) / 1024:.1f} KB)...")
    errors = []
    
    # Helper to retry with exponential backoff
    def _try_with_retries(func, name):
        for attempt in range(retries):
            try:
                print(f"  Trying {name}... (attempt {attempt + 1}/{retries})")
                return func()
            except Exception as e:
                errors.append(f"{name}: {e}")
                if attempt < retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"    Failed, retrying in {delay}s...")
                    time.sleep(delay)
        return None
    
    # transfer.sh (PUT)
    def _transfer_put():
        upload_url = f"https://transfer.sh/{filename}"
        resp = requests.put(upload_url, data=file_bytes, timeout=60)
        resp.raise_for_status()
        return resp.text.strip()
    
    link = _try_with_retries(_transfer_put, "transfer.sh")
    if link:
        print(f"✓ Upload successful: {link}")
        return link
    
    # anonfiles (POST JSON)
    def _anonfiles_post():
        resp = requests.post("https://api.anonfiles.com/upload", files={"file": (filename, file_bytes)}, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        if j.get("status") and j.get("data") and j["data"].get("file"):
            return j["data"]["file"]["url"]["full"]
        raise RuntimeError(f"Unexpected response: {j}")
    
    link = _try_with_retries(_anonfiles_post, "anonfiles")
    if link:
        print(f"✓ Upload successful: {link}")
        return link
    
    # 0x0.st (POST)
    def _0x0_post():
        resp = requests.post("https://0x0.st", files={"file": (filename, file_bytes)}, timeout=60)
        resp.raise_for_status()
        return resp.text.strip()
    
    link = _try_with_retries(_0x0_post, "0x0.st")
    if link:
        print(f"✓ Upload successful: {link}")
        return link
    
    # All attempts failed
    error_msg = "All upload attempts failed:\n  " + "\n  ".join(errors)
    raise RuntimeError(error_msg)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert any PDF to a shareable link.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_to_link.py document.pdf
  python pdf_to_link.py document.pdf --retries 5
        """
    )
    parser.add_argument("pdf_file", help="Path to the PDF file to upload.")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries per host (default: 3).")
    parser.add_argument("--delay", type=float, default=1.0, help="Base delay between retries in seconds (default: 1.0).")
    
    args = parser.parse_args()
    
    try:
        link = upload_pdf_to_host(args.pdf_file, retries=args.retries, base_delay=args.delay)
        print(f"\n🎉 Your PDF link: {link}")
        return 0
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
