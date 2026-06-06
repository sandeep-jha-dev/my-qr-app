import streamlit as st
import qrcode
from io import BytesIO

import streamlit as st
import qrcode
from io import BytesIO
import requests
import subprocess
import threading
import time
import sys
import os
import json
try:
    import boto3
except Exception:
    boto3 = None

# Sets up the webpage tab title
st.set_page_config(page_title="QR Generator")

st.title("🔗 Quick QR Code Generator")
st.write("Paste a link or upload a PDF. PDFs will be uploaded automatically and converted to a link for QR generation.")

# Input: either a URL/text or a PDF file
url_input = st.text_input("Enter URL or text (leave empty if uploading a PDF):")
uploaded_file = st.file_uploader("Upload a PDF (optional):", type=["pdf"])

# Hosting method selection
host_method = st.selectbox("Hosting method for uploaded PDFs:", ("auto-public-hosts", "s3", "save-local"), index=0, help="auto-public-hosts tries public services; s3 uses your S3-compatible storage; save-local stores file in the app folder (use ngrok to expose)")

# S3 credentials (only shown when user selects s3)
s3_access_key = s3_secret_key = s3_bucket = s3_region = s3_endpoint = None
if host_method == "s3":
    st.markdown("**S3 / Spaces credentials**")
    s3_access_key = st.text_input("Access Key", type="password")
    s3_secret_key = st.text_input("Secret Key", type="password")
    s3_bucket = st.text_input("Bucket name")
    s3_region = st.text_input("Region (optional)")
    s3_endpoint = st.text_input("Endpoint URL (optional, e.g. https://nyc3.digitaloceanspaces.com)")


def generate_qr_image_bytes(data: str) -> BytesIO:
    """Generate a QR code PNG in-memory and return a BytesIO."""
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def upload_file_to_host(file_bytes: bytes, filename: str) -> str:
    """Try multiple public hosts in order until one returns a link.

    Order: transfer.sh (PUT) -> anonfiles (API) -> 0x0.st (POST).
    Raises RuntimeError with combined errors if all attempts fail.
    """
    errors = []


    def _try_with_retries(func, name, attempts=3, base_delay=1):
        last_exc = None
        for i in range(attempts):
            try:
                return func()
            except Exception as e:
                last_exc = e
                delay = base_delay * (2 ** i)
                time.sleep(delay)
        errors.append(f"{name}: {last_exc}")
        return None

    # transfer.sh (PUT)
    def _transfer_put():
        upload_url = f"https://transfer.sh/{filename}"
        resp = requests.put(upload_url, data=file_bytes, timeout=60)
        resp.raise_for_status()
        return resp.text.strip()

    r = _try_with_retries(_transfer_put, "transfer.sh")
    if r:
        return r

    # anonfiles (POST JSON response)
    def _anonfiles_post():
        resp = requests.post("https://api.anonfiles.com/upload", files={"file": (filename, file_bytes)}, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        if j.get("status") and j.get("data") and j["data"].get("file"):
            return j["data"]["file"]["url"]["full"]
        raise RuntimeError(f"anonfiles: unexpected response {j}")

    r = _try_with_retries(_anonfiles_post, "anonfiles")
    if r:
        return r

    # 0x0.st (POST)
    def _0x0_post():
        resp = requests.post("https://0x0.st", files={"file": (filename, file_bytes)}, timeout=60)
        resp.raise_for_status()
        return resp.text.strip()

    r = _try_with_retries(_0x0_post, "0x0.st")
    if r:
        return r

    raise RuntimeError("All upload attempts failed: " + " | ".join(errors))


def upload_file_to_s3(file_bytes: bytes, filename: str, access_key: str, secret_key: str, bucket: str, region: str = None, endpoint_url: str = None) -> str:
    """Upload file to S3-compatible storage and return a presigned URL."""
    if boto3 is None:
        raise RuntimeError("boto3 is not installed; cannot upload to S3. Install boto3.")

    session = boto3.session.Session()
    client_kwargs = {}
    if region:
        client_kwargs["region_name"] = region
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    s3 = session.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        **client_kwargs,
    )

    from io import BytesIO as _BytesIO
    fileobj = _BytesIO(file_bytes)
    try:
        s3.upload_fileobj(fileobj, bucket, filename, ExtraArgs={"ContentType": "application/pdf"})
        # generate presigned URL (valid 7 days)
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": filename},
            ExpiresIn=7 * 24 * 3600,
        )
        return url
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}")


def start_local_http_server(uploads_dir: str, port: int = 8000):
    """Start a background local HTTP server serving `uploads_dir`. Returns Popen object."""
    if "local_server_proc" in st.session_state and st.session_state.local_server_proc:
        proc = st.session_state.local_server_proc
        if proc.poll() is None:
            return proc
    cmd = [sys.executable, "-m", "http.server", str(port), "--directory", uploads_dir]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    st.session_state.local_server_proc = proc
    return proc


def start_ngrok(port: int = 8000):
    """Start ngrok and return Popen object. ngrok must be installed and in PATH."""
    if "ngrok_proc" in st.session_state and st.session_state.ngrok_proc:
        proc = st.session_state.ngrok_proc
        if proc.poll() is None:
            return proc
    try:
        proc = subprocess.Popen(["ngrok", "http", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError("ngrok not found in PATH. Install ngrok and make sure it's available in PATH.")
    st.session_state.ngrok_proc = proc
    # give ngrok some time to start
    time.sleep(1)
    return proc


def get_ngrok_public_url():
    """Query ngrok's local API to retrieve the public tunnel URL."""
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels")
        resp.raise_for_status()
        data = resp.json()
        tunnels = data.get("tunnels", [])
        if not tunnels:
            return None
        # prefer https
        for t in tunnels:
            if t.get("proto") == "https":
                return t.get("public_url")
        return tunnels[0].get("public_url")
    except Exception:
        return None


if uploaded_file is not None:
    # User uploaded a PDF; automatically upload and QR-encode its shareable link
    file_bytes = uploaded_file.read()
    st.write(f"Uploaded: {uploaded_file.name} ({len(file_bytes)/1024:.1f} KB)")

    if host_method == "save-local":
        # Save locally to uploads/ and instruct user how to expose it
        import os
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        local_path = os.path.join(uploads_dir, uploaded_file.name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        st.success(f"Saved locally: {local_path}")
        st.info("To make this accessible from your phone, run a local HTTP server and expose it with ngrok.")
        st.code("python -m http.server 8000", language="bash")
        st.code("ngrok http 8000", language="bash")
        st.write("Place the uploaded file in the served folder (the 'uploads' folder). Then use the ngrok URL to generate the QR.")

        # Show QR for file:// path (informational only)
        file_url = f"file://{local_path}"
        qr_buf = generate_qr_image_bytes(file_url)
        st.image(qr_buf, caption="QR for local file path (only works on devices that can access this path)")
        st.download_button("📥 Download QR Code", data=qr_buf, file_name=f"{uploaded_file.name}.local_qr.png", mime="image/png")

    elif host_method == "s3":
        if not (s3_access_key and s3_secret_key and s3_bucket):
            st.warning("Enter S3 credentials and bucket to upload to S3.")
        else:
            with st.spinner("Uploading to S3..."):
                try:
                    link = upload_file_to_s3(file_bytes, uploaded_file.name, s3_access_key, s3_secret_key, s3_bucket, region=s3_region or None, endpoint_url=s3_endpoint or None)
                    st.success("Uploaded to S3 — shareable link below")
                    st.write(link)
                    qr_buf = generate_qr_image_bytes(link)
                    st.image(qr_buf, caption="QR for your PDF link")
                    st.download_button("📥 Download QR Code", data=qr_buf, file_name=f"{uploaded_file.name}.qr.png", mime="image/png")
                except Exception as e:
                    st.error(str(e))

    else:
        # auto-public-hosts fallback behaviour
        with st.spinner("Uploading PDF to public hosts to get a shareable link..."):
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
