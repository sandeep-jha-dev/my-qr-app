import streamlit as st
import qrcode
from io import BytesIO

import streamlit as st
import qrcode
from io import BytesIO
import base64
import requests

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator")

st.title("🔗 Quick QR Code Generator")

# Creates a text box for the user to type into
url = st.text_input("Enter your website link or text:")

def make_qr_and_buttons(data: str, download_name: str = "qrcode.png"):
    qr_img = qrcode.make(data)
    st.image(qr_img.get_image(), caption="Here is your QR Code!")

    img_bytes = BytesIO()
    qr_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    st.download_button(
        label="📥 Download QR Code",
        data=img_bytes,
        file_name=download_name,
        mime="image/png",
    )

# When the user types something, this block runs
if url:
    make_qr_and_buttons(url)

# Allow users to upload a PDF and (when possible) generate a QR for it
uploaded_file = st.file_uploader("Or upload a PDF to generate a QR for it:", type=["pdf"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    size_kb = len(file_bytes) / 1024
    st.write(f"Uploaded: {uploaded_file.name} ({size_kb:.1f} KB)")

    # Provide a download button for the original PDF
    st.download_button(
        label="📄 Download uploaded PDF",
        data=file_bytes,
        file_name=uploaded_file.name,
        mime="application/pdf",
    )

    # If the file is small enough, embed it as a data URL inside the QR
    EMBED_LIMIT = 2000  # bytes (base64-encoded PDF data will be larger)
    if len(file_bytes) <= EMBED_LIMIT:
        b64 = base64.b64encode(file_bytes).decode()
        data_url = f"data:application/pdf;base64,{b64}"
        st.success("File small enough — embedding PDF into QR as a data URL.")
        make_qr_and_buttons(data_url, download_name=f"{uploaded_file.name}.qr.png")
    else:
        st.info("File too large to embed directly into a QR code.")
        st.write("Options: upload to a temporary host to get a shareable link and encode that link in the QR.")

        col1, col2 = st.columns(2)
        if col1.button("Upload to transfer.sh (recommended)"):
            with st.spinner("Uploading to transfer.sh..."):
                try:
                    # transfer.sh accepts PUT to /<filename>
                    upload_url = f"https://transfer.sh/{uploaded_file.name}"
                    resp = requests.put(upload_url, data=file_bytes)
                    resp.raise_for_status()
                    link = resp.text.strip()
                    st.success("Uploaded — shareable link below")
                    st.write(link)
                    make_qr_and_buttons(link, download_name=f"{uploaded_file.name}.link_qr.png")
                except Exception as e:
                    st.error(f"transfer.sh upload failed: {e}")

        if col2.button("Upload to 0x0.st (fallback)"):
            with st.spinner("Uploading to 0x0.st..."):
                try:
                    resp = requests.post("https://0x0.st", files={"file": (uploaded_file.name, file_bytes)})
                    resp.raise_for_status()
                    link = resp.text.strip()
                    st.success("Uploaded — shareable link below")
                    st.write(link)
                    make_qr_and_buttons(link, download_name=f"{uploaded_file.name}.link_qr.png")
                except Exception as e:
                    st.error(f"0x0.st upload failed: {e}")
