#!/usr/bin/env python3
"""
Local PDF File Server
Host PDFs locally with a simple HTTP server and generate shareable links.
Can be used standalone or integrated with ngrok for external access.
"""

import sys
import os
import argparse
import http.server
import socketserver
import webbrowser
import threading
import time
from pathlib import Path
from urllib.parse import quote


def create_pdf_server(pdf_dir: str, port: int = 8000, host: str = "localhost"):
    """
    Create and start a simple HTTP server for serving PDFs from a directory.
    
    Args:
        pdf_dir: Directory containing PDF files to serve.
        port: Port to run server on (default 8000).
        host: Host to bind to (default "localhost").
        
    Returns:
        tuple: (server, thread) where thread is the running server thread.
    """
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        pdf_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {pdf_path}")
    
    os.chdir(pdf_path)
    
    class PDFHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # Block access to non-PDF files
            if self.path != "/" and not self.path.lower().endswith(".pdf"):
                self.send_response(403)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>403 Forbidden</h1><p>Only PDF files are allowed.</p>")
                return
            
            # Directory listing
            if self.path == "/" or self.path.endswith("/"):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                html = """
                <html>
                <head>
                    <title>PDF Server</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        a { color: #0066cc; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                        .file-list { margin-top: 20px; }
                        .file-item { padding: 8px; border-bottom: 1px solid #eee; }
                        .info { background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <h1>📄 PDF Server</h1>
                    <div class="info">
                        <p>Local PDF hosting. Share these links with others or use with QR codes.</p>
                    </div>
                    <div class="file-list">
                """
                
                # List PDF files
                pdf_files = sorted(Path(".").glob("*.pdf"))
                if pdf_files:
                    html += "<h2>Available PDFs:</h2>"
                    for pdf_file in pdf_files:
                        safe_name = quote(pdf_file.name)
                        size_mb = pdf_file.stat().st_size / (1024 * 1024)
                        html += f'<div class="file-item"><a href="/{safe_name}">{pdf_file.name}</a> ({size_mb:.1f} MB)</div>'
                else:
                    html += "<p><em>No PDF files found in this directory.</em></p>"
                
                html += """
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                return
            
            # Serve the file
            super().do_GET()
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    handler = PDFHandler
    server = socketserver.TCPServer((host, port), handler)
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    return server, thread


def copy_pdf_to_server(pdf_file: str, pdf_dir: str) -> str:
    """
    Copy a PDF file to the server directory.
    
    Args:
        pdf_file: Path to PDF file to copy.
        pdf_dir: Server directory to copy to.
        
    Returns:
        Filename in server directory.
    """
    pdf_path = Path(pdf_file)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")
    
    dest_dir = Path(pdf_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_file = dest_dir / pdf_path.name
    dest_file.write_bytes(pdf_path.read_bytes())
    
    return pdf_path.name


def get_pdf_url(filename: str, host: str = "localhost", port: int = 8000, use_https: bool = False) -> str:
    """Generate the full URL for a PDF file on the server."""
    protocol = "https" if use_https else "http"
    safe_name = quote(filename)
    return f"{protocol}://{host}:{port}/{safe_name}"


def main():
    parser = argparse.ArgumentParser(
        description="Host PDFs locally and generate shareable links.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server in current directory
  python pdf_to_link_server.py

  # Start server on custom port
  python pdf_to_link_server.py --port 9000

  # Add a PDF and get its link
  python pdf_to_link_server.py --add document.pdf

  # Use with ngrok for external access
  python pdf_to_link_server.py --ngrok-token YOUR_TOKEN
        """
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on (default: 8000).")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0).")
    parser.add_argument("--dir", default="pdfs", help="Directory to serve PDFs from (default: pdfs).")
    parser.add_argument("--add", help="Copy a PDF to server and print its link.")
    parser.add_argument("--ngrok-token", help="Use ngrok to expose server externally (requires ngrok auth token).")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser on startup.")
    
    args = parser.parse_args()
    
    try:
        # Handle --add mode (copy PDF and exit)
        if args.add:
            filename = copy_pdf_to_server(args.add, args.dir)
            url = get_pdf_url(filename, host=args.host, port=args.port)
            print(f"✓ PDF copied to server directory: {filename}")
            print(f"📎 Link: {url}")
            return 0
        
        # Start server
        print(f"🚀 Starting PDF Server on {args.host}:{args.port}...")
        server, thread = create_pdf_server(args.dir, port=args.port, host=args.host)
        
        # Display info
        local_url = f"http://localhost:{args.port}"
        print(f"✓ Server started successfully!")
        print(f"📍 Local access: {local_url}")
        
        # Optional ngrok
        if args.ngrok_token:
            try:
                import pyngrok
                from pyngrok import ngrok
                ngrok.set_auth_token(args.ngrok_token)
                public_url = ngrok.connect(args.port)
                print(f"🌐 Public access: {public_url}")
            except ImportError:
                print("⚠️  pyngrok not installed. Install with: pip install pyngrok")
            except Exception as e:
                print(f"⚠️  ngrok failed: {e}")
        
        # Open browser
        if not args.no_browser:
            print("🌐 Opening browser...")
            time.sleep(0.5)
            webbrowser.open(local_url)
        
        print(f"\n📁 Serving PDFs from: {args.dir}")
        print("💡 Copy PDFs to this folder, then access via the link above.")
        print("   Or use: python pdf_to_link_server.py --add /path/to/file.pdf")
        print("\nPress Ctrl+C to stop server.\n")
        
        # Keep server running
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
