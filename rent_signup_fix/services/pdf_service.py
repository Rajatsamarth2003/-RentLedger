from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


BASE_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = BASE_DIR / "fonts"
REGULAR_FONT = FONT_DIR / "NotoSans-Regular.ttf"
BOLD_FONT = FONT_DIR / "NotoSans-Bold.ttf"


def _register_fonts():
    """Register a Unicode font so the Indian Rupee symbol renders correctly."""
    if REGULAR_FONT.exists() and BOLD_FONT.exists():
        if "RentLedgerNoto" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RentLedgerNoto", str(REGULAR_FONT)))
        if "RentLedgerNoto-Bold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RentLedgerNoto-Bold", str(BOLD_FONT)))
        return "RentLedgerNoto", "RentLedgerNoto-Bold"

    # Safe fallback for environments where bundled fonts are missing.
    return "Helvetica", "Helvetica-Bold"


def money(value):
    return f"₹{value:,.2f}"


def generate_bill_pdf(bill, output_path):
    regular_font, bold_font = _register_fonts()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "BillTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=20,
        leading=24,
        spaceAfter=4
    )

    normal = ParagraphStyle(
        "BillNormal",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=10,
        leading=14
    )

    muted = ParagraphStyle(
        "Muted",
        parent=normal,
        fontSize=9,
        textColor=colors.HexColor("#64748b")
    )

    story = []

    story.append(Paragraph("MONTHLY RENT STATEMENT", title))
    story.append(Paragraph(
        f"<b>{bill['family_name']}</b> &nbsp; • &nbsp; {bill['month']}",
        normal
    ))
    story.append(Spacer(1, 10))

    data = [
        ["Meter & Billing Details", "Value"],
        ["Previous meter reading", f"{bill['previous_reading']:.0f}"],
        ["Current meter reading", f"{bill['current_reading']:.0f}"],
        ["Meter calculated units", f"{bill['calculated_units']:.0f}"],
        ["Units entered", f"{bill['entered_units']:.0f}"],
        ["Electricity rate", f"₹{bill['electricity_rate']:.0f} / unit"],
        ["Monthly rent", money(bill["rent"])],
        ["Electricity amount", money(bill["electricity_bill"])],
        ["TOTAL PAYABLE", money(bill["total_amount"])],
    ]

    table = Table(data, colWidths=[100 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), bold_font),
        ("FONTNAME", (0, 1), (-1, -1), regular_font),
        ("FONTNAME", (0, -1), (-1, -1), bold_font),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))

    difference = bill["entered_units"] - bill["calculated_units"]

    if abs(difference) < 0.01:
        check = "Cross-check: MATCH"
    else:
        check = f"Cross-check: {abs(difference):.0f} unit(s) difference"

    story.append(Paragraph(check, normal))
    story.append(Spacer(1, 8))

    ocr = (
        f"OCR reading: {bill['ocr_reading']:.0f}"
        if bill.get("ocr_reading") is not None
        else "OCR reading: Not available"
    )

    story.append(Paragraph(ocr, muted))
    story.append(Paragraph(
        "This statement stores the rent, rate and readings used for this month.",
        muted
    ))

    doc.build(story)
