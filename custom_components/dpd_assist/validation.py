"""Small, independently testable boundaries for current-image requests."""
import base64
import hashlib
import io
import re
from urllib.parse import urlsplit
from PIL import Image

def validate_picture(data, barcode, url):
    if not re.fullmatch(r"\d{14}", barcode):
        raise ValueError("Ungültige Paketnummer")
    location = urlsplit(url)
    if location.scheme != "https" or location.hostname != "my.dpd.de" or location.path.lower() != "/myparcels/dataprotection.aspx":
        raise ValueError("Es ist keine passende DPD-Prüfseite geöffnet")
    if not isinstance(data, str) or len(data) > 180000 or not data.startswith("data:image/png;base64,"):
        raise ValueError("Ungültiges CAPTCHA-Bild")
    raw = base64.b64decode(data.split(",", 1)[1], validate=True)
    if len(raw) > 128000:
        raise ValueError("Bild ist zu groß")
    with Image.open(io.BytesIO(raw)) as image:
        if image.format != "PNG" or not (30 <= image.width <= 800 and 15 <= image.height <= 300):
            raise ValueError("Unpassende Bildabmessungen")
        image.verify()
    return raw, hashlib.sha256(raw).hexdigest()

def validate_answer(result):
    data = result.get("data", {}) if isinstance(result, dict) else {}
    code = data.get("code", "") if isinstance(data, dict) else ""
    if not isinstance(code, str) or data.get("readable") is not True or not re.fullmatch(r"[A-Za-z0-9]{4,6}", code):
        raise ValueError("Die KI konnte das Bild nicht eindeutig lesen. Bitte eine neue Vorschau holen.")
    return code

def claim_request(requests, key, user_id, now):
    item = requests.get(key)
    if not item or item["user_id"] != user_id:
        raise ValueError("Keine passende Vorschau für diesen Benutzer vorhanden")
    if item["expires"] <= now:
        raise ValueError("Die Vorschau ist abgelaufen. Bitte neu holen.")
    if item["used"]:
        raise ValueError("Diese Vorschau wurde bereits bearbeitet")
    item["used"] = True
    return item
