# PDF to Link Converter

A simple Python tool to convert any PDF file into a shareable link. Use it as a CLI tool or import it as a module in your projects.

## Features

- Convert any PDF to a shareable link in seconds
- Works with public file hosting services:
  - `transfer.sh` (primary)
  - `anonfiles` (fallback)
  - `0x0.st` (fallback)
- Automatic retries with exponential backoff
- Both CLI and module interfaces
- Python 3.7+

## Installation

```bash
pip install requests
```

The `requests` library is the only dependency.

## Usage

### CLI Usage

Convert a single PDF:

```bash
python pdf_to_link.py document.pdf
```

With custom retry settings:

```bash
python pdf_to_link.py document.pdf --retries 5 --delay 2
```

The tool will output:
```
Uploading document.pdf (2.5 MB)...
  Trying transfer.sh... (attempt 1/3)
✓ Upload successful: https://transfer.sh/xyzabc/document.pdf

🎉 Your PDF link: https://transfer.sh/xyzabc/document.pdf
```

### Module Usage

Use `pdf_to_link.py` as a module in your Python code:

```python
from pdf_to_link import upload_pdf_to_host

try:
    link = upload_pdf_to_host("my_document.pdf")
    print(f"Your link: {link}")
except FileNotFoundError:
    print("PDF file not found")
except RuntimeError as e:
    print(f"Upload failed: {e}")
```

## CLI Options

```
positional arguments:
  pdf_file           Path to the PDF file to upload.

optional arguments:
  -h, --help         show this help message and exit
  --retries RETRIES  Number of retries per host (default: 3).
  --delay DELAY      Base delay between retries in seconds (default: 1.0).
```

## Examples

### Example 1: Simple upload
```bash
python pdf_to_link.py invoice.pdf
```

### Example 2: Increase retries for reliability
```bash
python pdf_to_link.py large_document.pdf --retries 5
```

### Example 3: Use in a Streamlit app
```python
import streamlit as st
from pdf_to_link import upload_pdf_to_host

uploaded_file = st.file_uploader("Upload PDF")
if uploaded_file:
    with st.spinner("Converting PDF to link..."):
        try:
            link = upload_pdf_to_host(uploaded_file)
            st.success(f"Link: {link}")
            st.code(link)
        except Exception as e:
            st.error(f"Failed: {e}")
```

## How It Works

1. **Read PDF**: Loads the PDF file from disk
2. **Try transfer.sh**: Attempts to upload via PUT request
3. **Retry if needed**: Waits with exponential backoff and retries
4. **Fallback to anonfiles**: If transfer.sh fails, tries anonfiles API
5. **Fallback to 0x0.st**: If anonfiles fails, tries 0x0.st
6. **Return link**: Returns the first successful shareable link

## Retry Strategy

The tool uses **exponential backoff** for reliability:
- Attempt 1: Immediate
- Attempt 2: Wait 1 second (default)
- Attempt 3: Wait 2 seconds
- And so on...

Custom delays:
```bash
python pdf_to_link.py document.pdf --retries 5 --delay 2
```

## Limitations

- **File size**: Most public hosts limit files to 100 MB - 5 GB
- **Expiration**: Files may expire (check each host's policy):
  - `transfer.sh`: 14 days (downloads reset timer)
  - `anonfiles`: 30+ days
  - `0x0.st`: Varies
- **Privacy**: Files are uploaded to public servers (not encrypted)
- **Network**: Requires internet connection

## For Private/Long-term Storage

If you need private or permanent links, consider:

1. **AWS S3**: Store PDFs with presigned URLs
2. **DigitalOcean Spaces**: Similar to S3, S3-compatible
3. **Your own server**: Host PDFs on your infrastructure
4. **Google Drive**: Share publicly via link

## Error Handling

The tool handles common errors:

```python
from pdf_to_link import upload_pdf_to_host

try:
    link = upload_pdf_to_host("document.pdf")
except FileNotFoundError:
    print("❌ File not found")
except RuntimeError as e:
    print(f"❌ Upload failed: {e}")
    print("   Check your internet connection or try later")
```

## Exit Codes

- `0`: Success
- `1`: File not found or upload failed

## Troubleshooting

### "Connection refused" or "Connection timeout"
- Check your internet connection
- Increase retries: `--retries 5`
- Increase delay: `--delay 3`
- Try later (servers may be down)

### "File not found"
- Check the file path: `python pdf_to_link.py /full/path/to/file.pdf`
- Use absolute paths for clarity

### "413 Payload Too Large"
- File exceeds host's size limit
- Break into smaller PDFs
- Use alternative hosting (S3, etc.)

## Performance

Typical upload times:
- 1 MB PDF: 2-5 seconds
- 10 MB PDF: 10-30 seconds
- 100 MB PDF: 1-5 minutes (depends on connection)

## License

MIT - Feel free to use and modify

## Contributing

Have ideas or improvements? Feel free to extend this tool!

## See Also

- **pdf_to_qr.py**: Combines this with QR code generation for easy sharing
- **QR Code Generator**: Web interface at `app.py` (Streamlit)
