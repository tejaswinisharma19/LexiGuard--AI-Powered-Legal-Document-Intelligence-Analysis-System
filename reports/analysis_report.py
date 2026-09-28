import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_analysis_pdf(document_name, analysis_data):
    """
    Generate a formatted PDF report for document analysis.
    Uses stored analysis history entry without invoking LLM or RAG pipeline.
    
    :param document_name: Name of the analyzed document (e.g., 'Employment_Agreement.pdf')
    :param analysis_data: Dictionary containing saved analysis fields (question, response, sources, timestamp)
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
    primary_color = colors.HexColor("#1e293b")  # Dark Slate
    secondary_color = colors.HexColor("#2563eb")  # Sapphire Blue
    text_color = colors.HexColor("#334155")
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#e2e8f0")

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
    story.append(Paragraph("LexiGuard Legal Intelligence Analysis Report", title_style))
    
    timestamp = analysis_data.get("timestamp", datetime.now(timezone.utc).isoformat())
    if "T" in timestamp:
        timestamp_formatted = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:8]
    else:
        timestamp_formatted = str(timestamp)

    story.append(Paragraph(f"<b>Document:</b> {document_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Generated:</b> {timestamp_formatted}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceAfter=15))

    # Metadata Card Table
    meta_data = [
        [Paragraph("<b>Report Type</b>", body_style), Paragraph(str(analysis_data.get("analysis_type", "Analysis")).upper(), body_style)],
        [Paragraph("<b>Target Document</b>", body_style), Paragraph(str(document_name), body_style)],
        [Paragraph("<b>Query / Scope</b>", body_style), Paragraph(str(analysis_data.get("question", "Comprehensive Analysis")), body_style)]
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

    # Executive Summary & Analysis Findings Section
    story.append(Paragraph("Analysis Findings & Insights", section_heading))
    
    response_text = analysis_data.get("response", "No analysis content available.")
    # Split response by double line breaks to form paragraphs cleanly
    paragraphs = [p.strip() for p in response_text.split("\n") if p.strip()]
    for p in paragraphs:
        # Escape XML special chars if needed, replace markdown bolding **text** with <b>text</b>
        formatted_p = p.replace("**", "<b>", 1)
        while "**" in formatted_p:
            formatted_p = formatted_p.replace("**", "</b>", 1)
        story.append(Paragraph(formatted_p, body_style))

    story.append(Spacer(1, 15))

    # Sources / References Section
    sources = analysis_data.get("sources", [])
    if sources:
        story.append(Paragraph("Referenced Document Sources", section_heading))
        source_rows = [
            [Paragraph("<b>Page #</b>", body_style), Paragraph("<b>Chunk #</b>", body_style), Paragraph("<b>Context / Reference Excerpt</b>", body_style)]
        ]
        for src in sources:
            pg = str(src.get("page_number", "N/A"))
            chk = str(src.get("chunk_number", "N/A"))
            txt = str(src.get("text", "Reference point verified in document text."))
            if len(txt) > 200:
                txt = txt[:197] + "..."
            source_rows.append([
                Paragraph(pg, body_style),
                Paragraph(chk, body_style),
                Paragraph(txt, body_style)
            ])
        
        src_table = Table(source_rows, colWidths=[50, 60, 420])
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
        "DISCLAIMER: LexiGuard is an AI-powered legal document intelligence tool. This report is generated automatically based on saved document analysis and is provided for informational and analytical purposes only. It does not constitute formal legal advice. Please consult a qualified legal professional for legal counsel.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
