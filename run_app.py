import streamlit as st
import time
from pathlib import Path
from qr_codec import prepare_file_for_transfer, generate_qr_pngs

BASE = Path("runtime")
UPLOAD = BASE / "uploads"
FRAMES = BASE / "frames"

for p in [UPLOAD, FRAMES]:
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(layout="wide")

mode = st.radio("Mode", ["Share", "Receive"])

# ---------------- SHARE ----------------
if mode == "Share":
    st.title("📤 QR Share - By Prajwal")

    file = st.file_uploader("Upload file")

    if file:
        path = UPLOAD / file.name
        with open(path, "wb") as f:
            f.write(file.getbuffer())

        st.success("Uploaded")

        if st.button("Start QR Streaming"):
            for f in FRAMES.glob("*"):
                f.unlink()

            data = prepare_file_for_transfer(path)
            frames = generate_qr_pngs(data["payloads"], FRAMES)

            st.session_state.frames = frames

    # # autoplay QR like video
    # if "frames" in st.session_state:
    #     placeholder = st.empty()
    #
    #     for img in st.session_state.frames:
    #         placeholder.image(str(img), width=600)
    #         time.sleep(0.7)   # ✅ stable speed

    def get_ordinal(n):
        # Dynamic suffix logic using standard math rules
        suffix = ["th", "st", "nd", "rd", "th"][
            min(n % 10, 4) if not (11 <= n % 100 <= 13) else 0]
        return f"{n}{suffix}"


    # autoplay QR like video
    if "frames" in st.session_state and st.session_state.frames:
        total_frames = len(st.session_state.frames)

        st.write(f"Frame contains {total_frames} images")

        text_placeholder = st.empty()
        image_placeholder = st.empty()

        while True:
            for idx, img in enumerate(st.session_state.frames, start=1):
                # Dynamic text generation without if/elif blocks
                ordinal_text = get_ordinal(idx)
                _, col, _ = st.columns([10,80,10])
                with col:
                    text_placeholder.markdown(f"**This is {ordinal_text} image**")
                    image_placeholder.image(str(img), width=600)
                    time.sleep(3)

# ---------------- RECEIVE ----------------
elif mode == "Receive":
    st.title("📥 QR Receiver (Auto Download)")

    # st.components.v1.html("""
    st.iframe("""
<script src="https://unpkg.com/html5-qrcode"></script>

<div id="reader" style="width:300px"></div>
<p id="status">Waiting for QR...</p>

<script>
let store = {
  sid: null,
  total: 0,
  received: {},
  meta: null
};

function decodeAndStore(text) {
    try {
        const data = JSON.parse(text);

        if (data.t === "meta") {
            store.sid = data.sid;
            store.total = data.total;
            store.meta = data;
            document.getElementById("status").innerText =
                "✅ Metadata received: " + data.total + " frames";
        }

        if (data.t === "chunk") {
            store.received[data.i] = data.data;

            document.getElementById("status").innerText =
                "📥 " + Object.keys(store.received).length + "/" + store.total;

            if (Object.keys(store.received).length === store.total) {
                reconstruct();
            }
        }
    } catch (e) {}
}

function reconstruct() {
    let full = "";

    for (let i = 0; i < store.total; i++) {
        full += store.received[i];
    }

    let binary = atob(full);
    let len = binary.length;
    let bytes = new Uint8Array(len);

    for (let i = 0; i < len; i++) {
        bytes[i] = binary.charCodeAt(i);
    }

    let blob = new Blob([bytes], { type: "application/octet-stream" });

    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = store.meta.name || "file";
    a.click();

    document.getElementById("status").innerText = "✅ Download complete";
}

const scanner = new Html5Qrcode("reader");

scanner.start(
    { facingMode: "environment" },
    { fps: 5, qrbox: 250 },
    (decodedText) => {
        decodeAndStore(decodedText);
    }
);
</script>
""", height=500)
    st.success("Point camera to QR stream")
