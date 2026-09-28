import re


def extract_meter_reading(image_path):
    """
    OCR helper for meter photos.

    OCR is deliberately treated as a cross-check, not the final billing value.
    The user can edit/confirm the detected reading before saving the bill.
    """
    try:
        import easyocr
    except ImportError:
        return {
            "reading": None,
            "confidence": None,
            "raw_text": "",
            "error": "EasyOCR is not installed. Run: pip install -r requirements.txt"
        }

    try:
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        results = reader.readtext(image_path)

        candidates = []

        for _, text, confidence in results:
            cleaned = re.sub(r"[^0-9.]", "", text)

            if not cleaned or cleaned.count(".") > 1:
                continue

            try:
                value = float(cleaned)
            except ValueError:
                continue

            if 0 <= value <= 999999:
                candidates.append((value, float(confidence), text))

        if not candidates:
            return {
                "reading": None,
                "confidence": None,
                "raw_text": " | ".join(str(item[1]) for item in results)
            }

        value, confidence, text = max(candidates, key=lambda item: item[1])

        return {
            "reading": value,
            "confidence": confidence,
            "raw_text": text
        }

    except Exception as exc:
        return {
            "reading": None,
            "confidence": None,
            "raw_text": "",
            "error": str(exc)
        }
