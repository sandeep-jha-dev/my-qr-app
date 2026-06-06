import streamlit as st
import qrcode
from io import BytesIO
import tempfile
import os
import base64

# Try to import the pdf_to_link converter
try:
    from pdf_to_link import upload_pdf_to_host
    PDF_CONVERTER_AVAILABLE = True
except ImportError:
    PDF_CONVERTER_AVAILABLE = False

# Try to import boto3 for S3 support
try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator", layout="wide")

st.title("🔗 Quick QR Code Generator")
st.write("Generate QR codes from URLs, text, or PDF files!")

# Initialize session state for settings
if "hosting_method" not in st.session_state:
    st.session_state.hosting_method = "s3" if S3_AVAILABLE else "data-url"

# Sidebar for configuration
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    hosting_method = st.radio(
        "PDF Hosting Method:",
        ("S3 / DigitalOcean Spaces", "Base64 Data URL", "Public Hosts"),
        help="Choose how to host uploaded PDFs for QR generation"
    )
    
    if hosting_method == "S3 / DigitalOcean Spaces":
        st.markdown("**S3/Spaces Credentials**")
        access_key = st.text_input("Access Key", type="password", key="s3_access")
        secret_key = st.text_input("Secret Key", type="password", key="s3_secret")
        bucket = st.text_input("Bucket Name", key="s3_bucket")
        region = st.text_input("Region (optional)", key="s3_region", placeholder="us-east-1")
        endpoint = st.text_input("Endpoint (optional)", key="s3_endpoint", placeholder="https://nyc3.digitaloceanspaces.com")
    else:
        access_key = secret_key = bucket = region = endpoint = None

# Function to upload to S3
def upload_to_s3(file_bytes, filename, access_key, secret_key, bucket, region=None, endpoint=None):
    """Upload file to S3 and return presigned URL."""
    if not all([access_key, secret_key, bucket]):
        raise ValueError("Missing S3 credentials")
    
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region
        if endpoint:
            client_kwargs["endpoint_url"] = endpoint
        
        s3 = session.client("s3", **client_kwargs)
        s3.put_object(Bucket=bucket, Key=filename, Body=file_bytes, ContentType="application/pdf")
        
        # Generate presigned URL (valid 7 days)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": filename},
            ExpiresIn=7 * 24 * 3600
        )
        return url
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}")

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

# Process URL/Text input
if url_input:
    st.divider()
    st.markdown("### Generated QR Code")
    generate_and_display_qr(url_input)

# Process PDF input
elif pdf_input:
    st.divider()
    
    # Show file info
    file_size_mb = pdf_input.size / (1024 * 1024)
    st.info(f"📦 File: {pdf_input.name} ({file_size_mb:.2f} MB)")
    
    # METHOD 1: S3/DigitalOcean Spaces
    if hosting_method == "S3 / DigitalOcean Spaces":
        if not S3_AVAILABLE:
            st.error("❌ boto3 not installed. Install with: pip install boto3")
        elif not all([access_key, secret_key, bucket]):
            st.warning("⚠️ Enter S3 credentials in the sidebar to upload PDFs.")
        else:
            try:
                with st.spinner("⏳ Uploading PDF to S3..."):
                    file_bytes = pdf_input.getbuffer()
                    link = upload_to_s3(
                        file_bytes,
                        pdf_input.name,
                        access_key,
                        secret_key,
                        bucket,
                        region=region or None,
                        endpoint=endpoint or None
                    )
                
                st.success("✅ PDF uploaded to S3!")
                st.write(f"**Shareable Link:** {link}")
                st.code(link, language="plaintext")
                
                st.markdown("### Generated QR Code")
                generate_and_display_qr(link, filename=f"{pdf_input.name}.qr.png")
                
            except Exception as e:
                st.error(f"❌ Error uploading to S3: {str(e)}")
    
    # METHOD 2: Base64 Data URL
    elif hosting_method == "Base64 Data URL":
        try:
            with st.spinner("⏳ Generating QR from PDF..."):
                file_bytes = pdf_input.getbuffer()
                # Encode PDF as base64
                b64 = base64.b64encode(file_bytes).decode()
                data_url = f"data:application/pdf;base64,{b64[:100]}..."  # Show truncated for UI
                
                st.success("✅ QR generated from PDF!")
                st.info("Note: QR contains the entire PDF as base64-encoded data. This works for small PDFs (< 2 MB).")
                
                # Generate QR for full data URL
                full_data_url = f"data:application/pdf;base64,{b64}"
                st.markdown("### Generated QR Code")
                generate_and_display_qr(full_data_url, filename=f"{pdf_input.name}.qr.png")
                
        except Exception as e:
            st.error(f"❌ Error generating QR: {str(e)}")
    
    # METHOD 3: Public Hosts (transfer.sh, etc.)
    else:
        if not PDF_CONVERTER_AVAILABLE:
            st.error("❌ PDF converter not available. Please ensure pdf_to_link.py is in the same directory.")
        else:
            try:
                with st.spinner("⏳ Uploading PDF to public hosts..."):
                    # Save PDF temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(pdf_input.getbuffer())
                        tmp_path = tmp_file.name
                    
                    # Convert PDF to link
                    link = upload_pdf_to_host(tmp_path, retries=2, base_delay=0.5)
                
                st.success("✅ PDF converted to link!")
                st.write(f"**Shareable Link:** {link}")
                st.code(link, language="plaintext")
                
                st.markdown("### Generated QR Code")
                generate_and_display_qr(link, filename=f"{pdf_input.name}.qr.png")
                
            except Exception as e:
                st.error(f"❌ Public hosts unavailable. Choose another hosting method in the sidebar. Error: {str(e)}")
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

else:
    st.info("👈 Enter a URL/text OR upload a PDF to get started!")
