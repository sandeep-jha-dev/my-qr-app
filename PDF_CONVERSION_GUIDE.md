# PDF to Link Converter - Complete Guide

I've created a complete suite of tools to convert any PDF to a shareable link. Choose the approach that works best for your needs.

## 📋 Overview of Tools

| Tool | Best For | Pros | Cons |
|------|----------|------|------|
| `pdf_to_link.py` | Quick CLI uploads | Simple, fast, no setup | Depends on public hosts |
| `pdf_to_link_server.py` | Local/private hosting | Reliable, private, flexible | Requires local server |
| `app.py` | Web UI with QR codes | User-friendly, visual | More dependencies |

---

## 1️⃣ Command-Line Tool: `pdf_to_link.py`

### Quick Start
```bash
python pdf_to_link.py mydocument.pdf
```

### Output Example
```
Uploading mydocument.pdf (2.5 MB)...
  Trying transfer.sh... (attempt 1/3)
✓ Upload successful: https://transfer.sh/abc123/mydocument.pdf

🎉 Your PDF link: https://transfer.sh/abc123/mydocument.pdf
```

### Features
- ✅ Works with public file hosts (transfer.sh, anonfiles, 0x0.st)
- ✅ Automatic retries with exponential backoff
- ✅ Clean CLI interface
- ✅ Usable as a Python module

### Usage Examples

#### Basic upload
```bash
python pdf_to_link.py report.pdf
```

#### More retries (for reliability)
```bash
python pdf_to_link.py report.pdf --retries 5
```

#### Increase backoff delay
```bash
python pdf_to_link.py report.pdf --delay 3
```

#### Use in Python code
```python
from pdf_to_link import upload_pdf_to_host

link = upload_pdf_to_host("document.pdf")
print(f"Share this link: {link}")

# Generate QR code
import qrcode
qr = qrcode.make(link)
qr.save("qr_code.png")
```

### Hosting Limits
- transfer.sh: 100 GB per file, 14 days expiration
- anonfiles: 5 GB per file, 30+ days expiration  
- 0x0.st: 100 MB - 5 GB, variable expiration

---

## 2️⃣ Local Server: `pdf_to_link_server.py`

### Quick Start
```bash
python pdf_to_link_server.py
```

This starts a local HTTP server and opens your browser to `http://localhost:8000`

### Features
- ✅ Host PDFs locally (no upload to external servers)
- ✅ Complete privacy (files stay on your computer)
- ✅ No file size limits (limited only by disk space)
- ✅ Optional ngrok integration for external access
- ✅ Automatic directory listing and file browsing

### Usage Modes

#### 1. Start server in default directory
```bash
python pdf_to_link_server.py
```
- Serves PDFs from `./pdfs` folder
- Opens browser automatically
- Access at http://localhost:8000

#### 2. Start on custom port
```bash
python pdf_to_link_server.py --port 9000
```

#### 3. Add a PDF and get its link
```bash
python pdf_to_link_server.py --add /path/to/document.pdf
```
Output:
```
✓ PDF copied to server directory: document.pdf
📎 Link: http://localhost:8000/document.pdf
```

#### 4. Use ngrok for external access (requires ngrok installed)
```bash
python pdf_to_link_server.py --ngrok-token YOUR_NGROK_AUTH_TOKEN
```
Output:
```
✓ Server started successfully!
📍 Local access: http://localhost:8000
🌐 Public access: https://abc123.ngrok.io
```

#### 5. Custom directory
```bash
python pdf_to_link_server.py --dir /path/to/pdf/folder
```

#### 6. Start without opening browser
```bash
python pdf_to_link_server.py --no-browser
```

### Workflow

**Simple local hosting:**
1. Run: `python pdf_to_link_server.py`
2. Drop PDFs in the `pdfs` folder
3. Share links from http://localhost:8000/filename.pdf

**Share with others (ngrok):**
1. Install ngrok: https://ngrok.com/download
2. Get auth token from https://dashboard.ngrok.com
3. Run: `python pdf_to_link_server.py --ngrok-token YOUR_TOKEN`
4. Share the public ngrok URL with others

---

## 3️⃣ Web UI with QR Codes: `app.py`

### Start
```bash
streamlit run app.py
```

Opens at http://localhost:8501

### Features
- ✅ Paste URLs or upload PDFs
- ✅ Generate QR codes automatically
- ✅ Download QR code images
- ✅ Multiple hosting options (public hosts, S3, local)
- ✅ Beautiful Streamlit UI

### Workflow
1. **For URLs/text**: Paste in the text box → QR generated instantly
2. **For PDFs**: Upload file → Auto-uploaded → QR generated for link

---

## 🎯 Recommended Workflows

### Workflow 1: Quick One-Off Upload
```bash
python pdf_to_link.py my_document.pdf
```
✅ Fastest for single files  
✅ No setup needed

### Workflow 2: Private Local Hosting
```bash
python pdf_to_link_server.py
# Drop PDFs in the pdfs/ folder
# Share from http://localhost:8000
```
✅ Complete privacy  
✅ No external services  
✅ Perfect for internal documents

### Workflow 3: Temporary Public Sharing (with ngrok)
```bash
# Terminal 1
python pdf_to_link_server.py --ngrok-token YOUR_TOKEN

# Terminal 2 (optional: generate QR)
python pdf_to_link.py /path/to/file.pdf
```
✅ External sharing when needed  
✅ Full control, no third-party uploads

### Workflow 4: Create QR Codes with Web UI
```bash
streamlit run app.py
```
✅ User-friendly interface  
✅ Visual QR generation  
✅ Multiple format support

### Workflow 5: Batch Convert Multiple PDFs
```bash
# Save to file then use in script
for f in *.pdf; do
    python pdf_to_link.py "$f" >> links.txt
done
```

---

## 🔧 Integration Examples

### Example 1: Python Script
```python
from pdf_to_link import upload_pdf_to_host
import qrcode

# Convert PDF to link
link = upload_pdf_to_host("invoice.pdf")

# Generate QR code
qr = qrcode.make(link)
qr.save("invoice_qr.png")

print(f"Link: {link}")
print("QR code saved as invoice_qr.png")
```

### Example 2: With Error Handling
```python
from pdf_to_link import upload_pdf_to_host

try:
    link = upload_pdf_to_host("document.pdf", retries=5)
    print(f"✓ Success: {link}")
except FileNotFoundError:
    print("❌ PDF not found")
except RuntimeError as e:
    print(f"❌ Upload failed: {e}")
```

### Example 3: Streamlit Integration
```python
import streamlit as st
from pdf_to_link import upload_pdf_to_host

st.title("Convert PDF to Link")
uploaded = st.file_uploader("Upload PDF")

if uploaded:
    with st.spinner("Converting..."):
        try:
            # Save temporarily
            with open("temp.pdf", "wb") as f:
                f.write(uploaded.getbuffer())
            
            link = upload_pdf_to_host("temp.pdf")
            st.success("Done!")
            st.write(f"**Link:** {link}")
            st.code(link)
        except Exception as e:
            st.error(f"Failed: {e}")
```

---

## 📊 Comparison Table

| Feature | pdf_to_link.py | pdf_to_link_server.py | app.py |
|---------|---|---|---|
| CLI interface | ✅ | ✅ | ❌ |
| Web UI | ❌ | ❌ (basic) | ✅ |
| Local hosting | ❌ | ✅ | ✅ |
| QR generation | ❌ | ❌ | ✅ |
| Public hosting | ✅ | ❌ | ✅ |
| S3/Spaces | ❌ | ❌ | ✅ |
| Easy to integrate | ✅ | ❌ | ❌ |
| No dependencies | ✅ | ✅ (except for ngrok) | ❌ |

---

## 🚀 Advanced Usage

### Batch Processing
```bash
# Convert all PDFs in a folder
for file in Documents/*.pdf; do
    python pdf_to_link.py "$file" --retries 5
done
```

### Automated Backups with Links
```bash
#!/bin/bash
BACKUP_DIR="./backups"
for backup in $BACKUP_DIR/*.pdf; do
    link=$(python pdf_to_link.py "$backup")
    echo "$(date): $backup -> $link" >> links_log.txt
done
```

### Server on Boot (using systemd)
Create `/etc/systemd/system/pdf-server.service`:
```ini
[Unit]
Description=PDF Link Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 pdf_to_link_server.py --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable pdf-server
sudo systemctl start pdf-server
```

---

## ❓ FAQs

**Q: Which tool should I use?**  
A: 
- Quick upload? → `pdf_to_link.py`
- Local hosting? → `pdf_to_link_server.py`
- Need QR codes? → `app.py`

**Q: How long do links last?**  
A: Depends on the host:
- transfer.sh: 14 days (extended by downloads)
- anonfiles: 30+ days
- 0x0.st: Variable
- Local server: As long as your computer runs

**Q: Can I host large PDFs?**  
A:
- Public hosts: Usually 100 MB - 5 GB
- Local server: Limited by your disk space

**Q: Is it secure?**  
A:
- Public hosts: Files are public (not encrypted)
- Local server: Private (as long as server not exposed)
- S3: Use private buckets with authentication

**Q: Can I integrate with my app?**  
A: Yes! Import `pdf_to_link.py` as a module:
```python
from pdf_to_link import upload_pdf_to_host
link = upload_pdf_to_host("file.pdf")
```

---

## 📝 Installation Summary

No additional installation needed for `pdf_to_link.py` beyond:
```bash
pip install requests
```

For full features:
```bash
pip install requests qrcode pillow streamlit boto3 pyngrok
```

For local server with ngrok:
```bash
pip install pyngrok
# Plus install ngrok from https://ngrok.com
```

---

## 🎓 Next Steps

1. **Try the CLI tool:**
   ```bash
   python pdf_to_link.py test.pdf
   ```

2. **Start a local server:**
   ```bash
   python pdf_to_link_server.py
   ```

3. **Generate QR codes:**
   ```bash
   streamlit run app.py
   ```

4. **Combine them:**
   - Use server to host PDFs locally
   - Use app.py to generate QR codes
   - Share QR codes with others

Enjoy converting PDFs to links! 🎉
