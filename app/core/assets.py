# app/core/assets.py
import requests, io
from PIL import Image

def load_ci_logo():
    urls = [
        "https://www.poscointl.com/images/main/logo_header.png",  # white on transparent
    ]
    for u in urls:
        r = None
        try:
            r = requests.get(u, timeout=6)
            if r.status_code == 200:
                return Image.open(io.BytesIO(r.content))
        except Exception:
            pass
        finally:
            if r is not None:
                r.close()
    return None
