import json, base64, zlib, hashlib
from pathlib import Path

class TransferStore:
    def __init__(self, base):
        self.base = base

    def save(self, text):
        data = json.loads(text)
        sid = data["sid"]

        folder = self.base / sid
        folder.mkdir(parents=True, exist_ok=True)

        meta_path = folder / "meta.json"

        if data["t"] == "meta":
            meta_path.write_text(json.dumps(data))
            return {"received": 0, "total": data["total"]}

        if data["t"] == "chunk":
            (folder / f"{data['i']}.txt").write_text(data["data"])

        meta = json.loads(meta_path.read_text())
        total = meta["total"]

        received = len(list(folder.glob("*.txt")))

        if received == total:
            self.assemble(sid)

        return {"received": received, "total": total}

    def assemble(self, sid):
        folder = self.base / sid
        meta = json.loads((folder / "meta.json").read_text())

        full = ""
        for i in range(meta["total"]):
            full += (folder / f"{i}.txt").read_text()

        data = base64.b64decode(full)

        try:
            data = zlib.decompress(data)
        except:
            pass

        if hashlib.sha256(data).hexdigest() != meta["sha"]:
            raise Exception("Integrity check failed")

        out = folder / meta["name"]
        out.write_bytes(data)

    def get_file(self, sid):
        folder = self.base / sid
        files = list(folder.glob("*.*"))
        for f in files:
            if not f.name.endswith(".txt") and f.name != "meta.json":
                return f
        return None
