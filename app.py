import streamlit as st
import qrcode
from io import BytesIO
import tempfile
import os

# Try to import the pdf_to_link converter
try:
    from pdf_to_link import upload_pdf_to_host
    PDF_CONVERTER_AVAILABLE = True
except ImportError:
    PDF_CONVERTER_AVAILABLE = False

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator", layout="wide")

st.title("🔗 Quick QR Code Generator")
st.write("Generate QR codes from URLs, text, or PDF files!")

# Create two columns for input options
col1, col2 = st.columns(2)

# OPTION 1: URL/Text input
with col1:
    st.subheader("📝 Option 1: URL or Text")
    url_input = st.text_input("Enter a website link or text:")

# OPTION 2: PDF upload
with col2:
    st.subheader("📄 Option 2: Upload a PDF")
    pdf_input = st.file_uploader("Choose a PDF file:", type=["pdf"])

# Function to generate and display QR code
def generate_and_display_qr(data: str, filename: str = "qrcode.png"):
    """Generate QR code from data and display with download button."""
    qr_img = qrcode.make(data)
    st.image(qr_img.get_image(), caption="Here is your QR Code!", width=300)
    
    # Convert image to bytes for download
    img_bytes = BytesIO()
    qr_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    st.download_button(
        label="📥 Download QR Code",
        data=img_bytes,
        file_name=filename,
        mime="image/png"
    )

# Process URL/Text input
if url_input:
    st.divider()
    st.markdown("### Generated QR Code")
    generate_and_display_qr(url_input)

# Process PDF input
elif pdf_input:
    st.divider()
    
    if not PDF_CONVERTER_AVAILABLE:
        st.error("❌ PDF converter not available. Please ensure pdf_to_link.py is in the same directory.")
    else:
        st.markdown("### Converting PDF to Link...")
        
        # Show file info
        file_size_mb = pdf_input.size / (1024 * 1024)
        st.info(f"📦 File: {pdf_input.name} ({file_size_mb:.2f} MB)")
        
        # Save PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_input.getbuffer())
            tmp_path = tmp_file.name
        
        try:
            with st.spinner("⏳ Uploading PDF and generating link..."):
                # Convert PDF to link
                link = upload_pdf_to_host(tmp_path, retries=3, base_delay=1.0)
            
            st.success("✅ PDF converted to link!")
            st.write(f"**Shareable Link:** {link}")
            st.code(link, language="plaintext")
            
            # Generate QR code for the PDF link
            st.markdown("### Generated QR Code")
            generate_and_display_qr(link, filename=f"{pdf_input.name}.qr.png")
            
        except Exception as e:
            st.error(f"❌ Error converting PDF: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass

else:
    st.info("👈 Enter a URL/text OR upload a PDF to get started!")
