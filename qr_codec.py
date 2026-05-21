import base64, zlib, hashlib, json, uuid
import qrcode
from pathlib import Path

def prepare_file_for_transfer(path: Path):
    raw = path.read_bytes()

    compressed = zlib.compress(raw)
    data = compressed if len(compressed) < len(raw) else raw

    sha = hashlib.sha256(raw).hexdigest()

    b64 = base64.b64encode(data).decode()

    chunk_size = 1500  # tuned to reduce frames
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

    sid = uuid.uuid4().hex[:10]

    # ✅ metadata first frame
    payloads = [json.dumps({
        "t": "meta",
        "sid": sid,
        "total": len(chunks),
        "name": path.name,
        "sha": sha
    })]

    for i, c in enumerate(chunks):
        payloads.append(json.dumps({
            "t": "chunk",
            "sid": sid,
            "i": i,
            "data": c
        }))

    return {"payloads": payloads, "session": sid}

def generate_qr_pngs(payloads, out: Path):
    out.mkdir(exist_ok=True)
    frames = []

    for i, p in enumerate(payloads):
        img = qrcode.make(p)
        path = out / f"frame_{i}.png"
        img.save(path)
        frames.append(path)

    return frames
