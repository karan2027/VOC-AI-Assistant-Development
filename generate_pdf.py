import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#64748b"))
            
            # Header
            self.drawString(54, 800, "VaultofCodes — AI Assistant Development")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(541, 30, page_text)
            self.drawString(54, 30, "Developer: Chhotelal Kushwaha")
            self.line(54, 42, 541, 42)
            
            self.restoreState()

def build_pdf():
    pdf_filename = "d:/SEMESTER/Seventh(7th) Semester/VaultOfCode/Assignment 3(Project)/AI_Assistant_Development.pdf"
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        alignment=1, # Centered
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=15
    )
    
    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#00a884"),
        spaceAfter=25
    )
    
    cover_meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#334155"),
        spaceAfter=20
    )
    
    link_style = ParagraphStyle(
        'CoverLink',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1Title',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=20
    )

    h2_style = ParagraphStyle(
        'H2Title',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#009677"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=1, # Centered
        textColor=colors.HexColor("#334155"),
        spaceAfter=12
    )

    img_title_style = ParagraphStyle(
        'ImgTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10
    )

    story = []

    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 140))
    story.append(Paragraph("AI Assistant Development", cover_title_style))
    story.append(Paragraph("VaultofCodes College Project", cover_subtitle_style))
    
    story.append(HRFlowable(width="50%", thickness=2, color=colors.HexColor("#00d4aa"), spaceAfter=30, spaceBefore=10))
    
    story.append(Paragraph("<b>Developer & Creator:</b> Chhotelal Kushwaha", cover_meta_style))
    story.append(Spacer(1, 15))
    
    github_link = "https://github.com/karan2027/VOC-AI-Assistant-Development"
    linkedin_link = "https://www.linkedin.com/posts/chhotelal-kushwaha-2902a3329_vaultofcodes-promptengineering-artificialintelligence-activity-7486847656430940160-oi-f?utm_source=share&utm_medium=member_android&rcm=ACoAAFLNZ8wBTSjgCxbdn5SefSpljH7s0IzWm0k"

    story.append(Paragraph(f"<b>GitHub Repository Link:</b><br/><a href='{github_link}' color='#0284c7'>{github_link}</a>", link_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>LinkedIn Activity Post Link:</b><br/><a href='{linkedin_link}' color='#0284c7'>{linkedin_link}</a>", link_style))
    
    story.append(PageBreak())

    # ================= PAGE 2: PROJECT DETAILS =================
    story.append(Spacer(1, 50))
    story.append(Paragraph("Project Details & Summary", h1_style))
    story.append(HRFlowable(width="70%", thickness=1.5, color=colors.HexColor("#00d4aa"), spaceAfter=25))

    story.append(Paragraph("<b>VaultofCodes AI Assistant</b> is a full-stack, web-based Artificial Intelligence application engineered to deliver intelligent conversational capabilities, dynamic text summarization, creative content generation, and tailored step-by-step advice.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Core Capabilities & Requirements Fulfilled:</b>", h2_style))
    story.append(Paragraph("• <b>Factual Q&A:</b> Provides concise and accurate answers to general knowledge and technical questions.<br/>"
                           "• <b>Text Summarization:</b> Extracts executive summaries and structured bullet points from long paragraphs.<br/>"
                           "• <b>Creative Content Generation:</b> Writes imaginative stories, poems, speeches, and creative texts.<br/>"
                           "• <b>Suggestions & Advice:</b> Generates practical, structured coaching and actionable recommendations.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Technical Architecture & Stack:</b>", h2_style))
    story.append(Paragraph("• <b>Backend Framework:</b> Python 3 & Flask REST API Service.<br/>"
                           "• <b>AI Core Engine:</b> Google Gemini API (v1beta REST) with Multi-Provider Fallback.<br/>"
                           "• <b>Frontend Interface:</b> Responsive HTML5, Vanilla CSS3 (Dark Glassmorphic Theme), JavaScript (ES6+).", body_style))
    
    story.append(PageBreak())

    # ================= PAGE 3: ALL 4 PHOTOS ON A SINGLE PAGE =================
    story.append(Paragraph("Project Screenshots Overview", h1_style))
    story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor("#00d4aa"), spaceAfter=15))

    output_dir = "d:/SEMESTER/Seventh(7th) Semester/VaultOfCode/Assignment 3(Project)/output"
    
    # 2x2 Grid Table of all 4 images on Page 3
    img_w = 230
    img_h = 125
    
    img1 = Image(os.path.join(output_dir, "op1.PNG"), width=img_w, height=img_h)
    img2 = Image(os.path.join(output_dir, "op2.PNG"), width=img_w, height=img_h)
    img3 = Image(os.path.join(output_dir, "op3.PNG"), width=img_w, height=img_h)
    img4 = Image(os.path.join(output_dir, "op4.PNG"), width=img_w, height=img_h)

    caption_style = ParagraphStyle('Cap', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, alignment=1, textColor=colors.HexColor("#0f172a"))

    grid_data = [
        [img1, img2],
        [Paragraph("1. Main UI (Home)", caption_style), Paragraph("2. Factual Q&A", caption_style)],
        [img3, img4],
        [Paragraph("3. List Generation", caption_style), Paragraph("4. Text Summarization", caption_style)]
    ]

    t = Table(grid_data, colWidths=[240, 240])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    story.append(t)
    story.append(PageBreak())

    # ================= PAGES 4-7: INDIVIDUAL FULL-PAGE SCREENSHOTS =================
    full_images = [
        ("op1.PNG", "Output 1: Main Application Interface (Home View)"),
        ("op2.PNG", "Output 2: Factual Q&A Mode — Artificial Intelligence Query"),
        ("op3.PNG", "Output 3: Data Formatting & List Generation (10 Birds Name)"),
        ("op4.PNG", "Output 4: Text Summarization Mode — DBMS Executive Summary")
    ]

    for filename, title in full_images:
        story.append(Spacer(1, 10))
        story.append(Paragraph(title, img_title_style))
        story.append(Spacer(1, 10))
        img_path = os.path.join(output_dir, filename)
        img_full = Image(img_path, width=480, height=260)
        story.append(img_full)
        story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
