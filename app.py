import base64, json, zlib, uuid, hashlib
import qrcode
from pathlib import Path

def prepare_file_for_transfer(path: Path):
    raw = path.read_bytes()

    compressed = zlib.compress(raw)
    data = compressed if len(compressed) < len(raw) else raw

    b64 = base64.b64encode(data).decode()

    chunk_size = 1400  # optimized
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

    sid = uuid.uuid4().hex[:10]

    sha = hashlib.sha256(raw).hexdigest()

    payloads = [json.dumps({
        "t": "meta",
        "sid": sid,
        "total": len(chunks),
        "name": path.name,
        "sha": sha
    })]

    for i, chunk in enumerate(chunks):
        payloads.append(json.dumps({
            "t": "chunk",
            "sid": sid,
            "i": i,
            "data": chunk
        }))

    return {"payloads": payloads}

def generate_qr_pngs(payloads, out: Path):
    out.mkdir(exist_ok=True)

    paths = []
    for i, p in enumerate(payloads):
        img = qrcode.make(p)
        file = out / f"{i}.png"
        img.save(file)
        paths.append(file)

    return paths