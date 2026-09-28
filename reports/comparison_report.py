import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_comparison_pdf(comparison_data):
    """
    Generate a formatted PDF report for document comparison.
    Uses the exact saved comparison output produced by the existing comparison engine
    without invoking LLM or RAG pipeline or altering comparison categories.
    
    :param comparison_data: Dictionary containing comparison history entry
    :return: BytesIO buffer containing the PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    primary_color = colors.HexColor("#0f172a")  # Deep Navy
    secondary_color = colors.HexColor("#0d9488")  # Teal Accent
    text_color = colors.HexColor("#334155")
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=text_color,
        spaceAfter=8
    )

    disclaimer_style = ParagraphStyle(
        "DisclaimerStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#94a3b8"),
        spaceBefore=15
    )

    story = []

    # Title Banner
    story.append(Paragraph("LexiGuard Document Comparison Report", title_style))

    timestamp = comparison_data.get("timestamp", datetime.now(timezone.utc).isoformat())
    if "T" in timestamp:
        timestamp_formatted = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:8]
    else:
        timestamp_formatted = str(timestamp)

    doc_a_name = comparison_data.get("document_a", {}).get("filename", "Document A")
    doc_b_name = comparison_data.get("document_b", {}).get("filename", "Document B")

    story.append(Paragraph(f"<b>Generated:</b> {timestamp_formatted} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Report ID:</b> {comparison_data.get('comparison_id', 'N/A')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceAfter=15))

    # Compared Documents Table
    meta_data = [
        [Paragraph("<b>Document A</b>", body_style), Paragraph(str(doc_a_name), body_style)],
        [Paragraph("<b>Document B</b>", body_style), Paragraph(str(doc_b_name), body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[130, 400])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Comparison Results Section
    story.append(Paragraph("Comparative Analysis Results", section_heading))

    response_text = comparison_data.get("response", "No comparison results available.")
    paragraphs = [p.strip() for p in response_text.split("\n") if p.strip()]
    for p in paragraphs:
        formatted_p = p.replace("**", "<b>", 1)
        while "**" in formatted_p:
            formatted_p = formatted_p.replace("**", "</b>", 1)
        story.append(Paragraph(formatted_p, body_style))

    story.append(Spacer(1, 15))

    # Sources / References Section
    sources = comparison_data.get("sources", [])
    if sources:
        story.append(Paragraph("Verified Citation Excerpts", section_heading))
        source_rows = [
            [Paragraph("<b>Document / Source</b>", body_style), Paragraph("<b>Page #</b>", body_style), Paragraph("<b>Excerpt</b>", body_style)]
        ]
        for src in sources:
            doc_label = str(src.get("document", "Source Text"))
            pg = str(src.get("page_number", "N/A"))
            txt = str(src.get("text", "Reference point verified."))
            if len(txt) > 200:
                txt = txt[:197] + "..."
            source_rows.append([
                Paragraph(doc_label, body_style),
                Paragraph(pg, body_style),
                Paragraph(txt, body_style)
            ])

        src_table = Table(source_rows, colWidths=[120, 50, 360])
        src_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(src_table)
        story.append(Spacer(1, 15))

    # Disclaimer Section
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=10, spaceAfter=10))
    story.append(Paragraph(
        "DISCLAIMER: LexiGuard is an AI-powered legal document intelligence system. This document comparison report is produced automatically from stored analysis data and is provided for analytical context only. It does not constitute binding legal counsel.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
