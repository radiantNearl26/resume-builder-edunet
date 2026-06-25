from __future__ import annotations

from io import BytesIO
from textwrap import wrap

try:  # pragma: no cover - optional dependency
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:  # pragma: no cover - optional dependency fallback
    colors = None
    A4 = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    inch = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

from ..core.schemas import ResumeData

def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br />"), style)


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_fallback_pdf(lines: list[str]) -> bytes:
    wrapped_lines: list[str] = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(wrap(cleaned, width=90) or [cleaned])

    content_lines = ["BT", "/F1 11 Tf", "1 0 0 1 50 780 Tm", "14 TL"]
    first = True
    for line in wrapped_lines[:45]:
        if first:
            content_lines.append(f"({_escape_pdf_text(line)}) Tj")
            first = False
        else:
            content_lines.extend(["T*", f"({_escape_pdf_text(line)}) Tj"])
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1")

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(f"5 0 obj << /Length {len(content)} >> stream\n".encode("latin-1") + content + b"\nendstream endobj\n")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            "trailer << /Size {size} /Root 1 0 R >>\n"
            "startxref\n"
            "{xref}\n"
            "%%EOF\n"
        ).format(size=len(offsets), xref=xref_position).encode("latin-1")
    )
    return bytes(pdf)


def generate_resume_pdf(resume: ResumeData, score_report: dict[str, object], template_name: str = "modern") -> bytes:
    if SimpleDocTemplate is None:
        personal = resume.personal_info
        lines = [
            personal.full_name,
            " | ".join(
                part
                for part in [personal.title, personal.location, personal.email, personal.phone, personal.linkedin or "", personal.portfolio or ""]
                if part
            ),
            "",
            "Summary",
            resume.summary.strip(),
        ]
        for item in resume.experience:
            lines.extend([f"Experience: {item.title} - {item.company}"])
            lines.extend([f"- {bullet}" for bullet in [*item.bullets, *item.achievements] if bullet.strip()])
        for item in resume.education:
            lines.extend([f"Education: {item.degree} - {item.institution}"])
        if any([resume.skills.technical, resume.skills.tools, resume.skills.soft_skills]):
            lines.append("Skills: " + ", ".join([*resume.skills.technical, *resume.skills.tools, *resume.skills.soft_skills]))
        for item in resume.projects:
            lines.append(f"Project: {item.name}")
        for item in resume.certifications:
            lines.append(f"Certification: {item.name} - {item.issuer}")
        return _build_fallback_pdf(lines)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8,
    )
    heading_style = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        spaceAfter=4,
    )

    personal = resume.personal_info
    story: list = []
    story.append(_paragraph(personal.full_name, title_style))
    contact = " | ".join(
        part
        for part in [personal.title, personal.location, personal.email, personal.phone, personal.linkedin or "", personal.portfolio or ""]
        if part
    )
    story.append(_paragraph(contact, body_style))
    story.append(Spacer(1, 0.12 * inch))

    if resume.summary.strip():
        story.append(_paragraph("Summary", heading_style))
        story.append(_paragraph(resume.summary.strip(), body_style))

    if resume.experience:
        story.append(_paragraph("Experience", heading_style))
        for item in resume.experience:
            story.append(_paragraph(f"<b>{item.title}</b> - {item.company} ({item.start_date} to {item.end_date or 'Present'})", body_style))
            for bullet in [*item.bullets, *item.achievements]:
                if bullet.strip():
                    story.append(_paragraph(f"• {bullet.strip()}", body_style))

    if resume.education:
        story.append(_paragraph("Education", heading_style))
        for item in resume.education:
            line = f"<b>{item.degree}</b> - {item.institution} ({item.start_date} to {item.end_date or 'Present'})"
            story.append(_paragraph(line, body_style))
            if item.coursework:
                story.append(_paragraph(f"Coursework: {item.coursework}", body_style))

    if any([resume.skills.technical, resume.skills.tools, resume.skills.soft_skills]):
        story.append(_paragraph("Skills", heading_style))
        skills_lines = []
        if resume.skills.technical:
            skills_lines.append("Technical: " + ", ".join(resume.skills.technical))
        if resume.skills.tools:
            skills_lines.append("Tools: " + ", ".join(resume.skills.tools))
        if resume.skills.soft_skills:
            skills_lines.append("Soft Skills: " + ", ".join(resume.skills.soft_skills))
        for line in skills_lines:
            story.append(_paragraph(line, body_style))

    if resume.projects:
        story.append(_paragraph("Projects", heading_style))
        for item in resume.projects:
            story.append(_paragraph(f"<b>{item.name}</b>", body_style))
            for part in [item.tech_stack, item.description, item.impact]:
                if part.strip():
                    story.append(_paragraph(f"• {part.strip()}", body_style))

    if resume.certifications:
        story.append(_paragraph("Certifications", heading_style))
        for item in resume.certifications:
            story.append(_paragraph(f"• {item.name} - {item.issuer} {f'({item.date_obtained})' if item.date_obtained else ''}", body_style))

    doc.build(story)
    return buffer.getvalue()
