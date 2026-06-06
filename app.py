import streamlit as st
import qrcode
from io import BytesIO

import streamlit as st
import qrcode
from io import BytesIO
import requests

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator")

st.title("🔗 Quick QR Code Generator")
st.write("Paste a link or upload a PDF. PDFs will be uploaded automatically and converted to a link for QR generation.")

# Input: either a URL/text or a PDF file
url_input = st.text_input("Enter URL or text (leave empty if uploading a PDF):")
uploaded_file = st.file_uploader("Upload a PDF (optional):", type=["pdf"])


def generate_qr_image_bytes(data: str) -> BytesIO:
    """Generate a QR code PNG in-memory and return a BytesIO."""
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def upload_file_to_host(file_bytes: bytes, filename: str) -> str:
    """Try transfer.sh first, then fallback to 0x0.st. Returns the public link or raises."""
    # Try transfer.sh (PUT)
    try:
        upload_url = f"https://transfer.sh/{filename}"
        resp = requests.put(upload_url, data=file_bytes, timeout=60)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception:
        # Fallback to 0x0.st (POST)
        try:
            resp = requests.post("https://0x0.st", files={"file": (filename, file_bytes)}, timeout=60)
            resp.raise_for_status()
            return resp.text.strip()
        except Exception as e:
            raise RuntimeError(f"Upload failed: {e}")


if uploaded_file is not None:
    # User uploaded a PDF; automatically upload and QR-encode its shareable link
    file_bytes = uploaded_file.read()
    st.write(f"Uploaded: {uploaded_file.name} ({len(file_bytes)/1024:.1f} KB)")
    with st.spinner("Uploading PDF to get a shareable link..."):
        try:
            link = upload_file_to_host(file_bytes, uploaded_file.name)
            st.success("Upload complete — shareable link below")
            st.write(link)

            qr_buf = generate_qr_image_bytes(link)
            st.image(qr_buf, caption="QR for your PDF link")
            st.download_button("📥 Download QR Code", data=qr_buf, file_name=f"{uploaded_file.name}.qr.png", mime="image/png")
        except Exception as e:
            st.error(str(e))

elif url_input:
    # User provided a link or text; directly generate QR
    qr_buf = generate_qr_image_bytes(url_input)
    st.image(qr_buf, caption="Here is your QR Code!")
    st.download_button("📥 Download QR Code", data=qr_buf, file_name="qrcode.png", mime="image/png")

else:
    st.info("Enter a URL or upload a PDF to generate a QR code.")
