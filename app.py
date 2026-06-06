import streamlit as st
import qrcode
from io import BytesIO

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator")

st.title("🔗 Quick QR Code Generator")

# Creates a text box for the user to type into
url = st.text_input("Enter your website link or text:")

# When the user types something, this block runs
if url:
    # Create the QR code
    qr_img = qrcode.make(url)
    
    # Display it directly on the website
    st.image(qr_img.get_image(), caption="Here is your QR Code!")
    
    # Convert image to bytes for download
    img_bytes = BytesIO()
    qr_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    # Add download button
    st.download_button(
        label="Download QR Code",
        data=img_bytes,
        file_name="qrcode.png",
        mime="image/png"
    )
