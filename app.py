import streamlit as st
import time
import base64
from pathlib import Path
from qr_codec import prepare_file_for_transfer, generate_qr_pngs
from storage import TransferStore

BASE = Path("runtime")
UPLOAD = BASE / "uploads"
SHARE = BASE / "frames"
RECV = BASE / "received"

for p in [UPLOAD, SHARE, RECV]:
    p.mkdir(parents=True, exist_ok=True)

store = TransferStore(RECV)

st.set_page_config(layout="wide")

mode = st.radio("Select Mode", ["Share", "Receive"])

# ---------------- SHARE ----------------
if mode == "Share":
    st.title("📤 QR Share")

    uploaded = st.file_uploader("Upload file")

    if uploaded:
        file_path = UPLOAD / uploaded.name
        with open(file_path, "wb") as f:
            f.write(uploaded.getbuffer())

        st.success("File uploaded")

        if st.button("Generate + Play QR"):
            for f in SHARE.glob("*.png"):
                f.unlink()

            data = prepare_file_for_transfer(file_path)
            frames = generate_qr_pngs(data["payloads"], SHARE)

            st.success(f"{len(frames)} QR frames created")

            placeholder = st.empty()

            # autoplay loop
            while True:
                for img in frames:
                    placeholder.image(str(img), width=400)
                    time.sleep(0.15)

# ---------------- RECEIVE ----------------
elif mode == "Receive":
    st.title("📥 QR Receiver")

    st.components.v1.html("""
    <script src="https://unpkg.com/html5-qrcode"></script>

    <div id="reader" style="width:300px"></div>
    <p id="status">Scanning...</p>

    <script>
    const qr = new Html5Qrcode("reader");

    function onScanSuccess(decodedText) {
        fetch("/qr", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text: decodedText})
        }).then(r => r.json()).then(d => {
            document.getElementById("status").innerText =
                `Received: ${d.received}/${d.total}`;
        });
    }

    qr.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        onScanSuccess
    );
    </script>
    """, height=400)

    st.info("After full scan, download will appear below")

    sid = st.text_input("Session ID")

    if st.button("Download File"):
        file = store.get_file(sid)
        if file:
            with open(file, "rb") as f:
                st.download_button("Download", f, file.name)