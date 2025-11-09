#!/usr/bin/env python3
"""
Generate a realistic LinkedIn profile PDF template.
This creates a sample LinkedIn profile export that users can use as a template.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os
import sys

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_linkedin_template(output_path):
    """Create a LinkedIn profile PDF template."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for the 'Flowable' objects
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0077B5'),  # LinkedIn blue
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0077B5'),
        spaceAfter=12,
        spaceBefore=20,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=14
    )

    # Header Section
    story.append(Paragraph("John Doe", title_style))
    story.append(Paragraph("Software Engineer | Full Stack Developer | AI Enthusiast", subtitle_style))
    story.append(Paragraph("📍 San Francisco Bay Area, CA • <a href='mailto:john.doe@example.com'>john.doe@example.com</a>", body_style))
    story.append(Spacer(1, 0.2*inch))

    # About Section
    story.append(Paragraph("About", heading_style))
    about_text = """
    Passionate software engineer with 5+ years of experience building scalable web applications
    and cloud-based solutions. Specialized in full-stack development with expertise in Python,
    JavaScript, and modern frameworks. Strong background in AI/ML integration and cloud architecture.
    Always eager to learn new technologies and contribute to innovative projects.
    """
    story.append(Paragraph(about_text.strip(), body_style))
    story.append(Spacer(1, 0.1*inch))

    # Experience Section
    story.append(Paragraph("Experience", heading_style))

    # Experience 1
    story.append(Paragraph("<b>Senior Software Engineer</b>", body_style))
    story.append(Paragraph("Tech Company Inc. • Full-time", subtitle_style))
    story.append(Paragraph("Jan 2021 - Present • 3 years 10 months", body_style))
    exp1_text = """
    • Led development of microservices architecture serving 1M+ daily active users
    • Designed and implemented RESTful APIs using Python/FastAPI and Node.js
    • Collaborated with cross-functional teams to deliver features on time and within budget
    • Mentored junior developers and conducted code reviews
    • Improved system performance by 40% through optimization and caching strategies
    """
    story.append(Paragraph(exp1_text.strip(), body_style))
    story.append(Spacer(1, 0.15*inch))

    # Experience 2
    story.append(Paragraph("<b>Software Engineer</b>", body_style))
    story.append(Paragraph("StartupXYZ • Full-time", subtitle_style))
    story.append(Paragraph("Jun 2019 - Dec 2020 • 1 year 7 months", body_style))
    exp2_text = """
    • Developed and maintained web applications using React, Node.js, and PostgreSQL
    • Implemented CI/CD pipelines using Docker and AWS services
    • Participated in agile development processes and sprint planning
    • Fixed critical bugs and improved application stability
    """
    story.append(Paragraph(exp2_text.strip(), body_style))
    story.append(Spacer(1, 0.15*inch))

    # Experience 3
    story.append(Paragraph("<b>Junior Developer</b>", body_style))
    story.append(Paragraph("Web Solutions LLC • Full-time", subtitle_style))
    story.append(Paragraph("Jul 2018 - May 2019 • 11 months", body_style))
    exp3_text = """
    • Built responsive web interfaces using HTML, CSS, and JavaScript
    • Assisted in backend development using Python and Django
    • Learned best practices in software development and version control
    """
    story.append(Paragraph(exp3_text.strip(), body_style))
    story.append(Spacer(1, 0.2*inch))

    # Education Section
    story.append(Paragraph("Education", heading_style))

    story.append(Paragraph("<b>Bachelor of Science in Computer Science</b>", body_style))
    story.append(Paragraph("University of California, Berkeley", subtitle_style))
    story.append(Paragraph("2014 - 2018", body_style))
    edu_text = """
    Relevant coursework: Data Structures, Algorithms, Database Systems, Software Engineering,
    Machine Learning, Distributed Systems
    """
    story.append(Paragraph(edu_text.strip(), body_style))
    story.append(Spacer(1, 0.2*inch))

    # Skills Section
    story.append(Paragraph("Skills", heading_style))

    skills_data = [
        ['Programming Languages', 'Python • JavaScript • TypeScript • Java • Go'],
        ['Frameworks & Libraries', 'React • Node.js • FastAPI • Django • Express.js'],
        ['Databases', 'PostgreSQL • MongoDB • Redis • MySQL'],
        ['Cloud & DevOps', 'AWS • Docker • Kubernetes • CI/CD • Terraform'],
        ['Tools & Technologies', 'Git • Linux • REST APIs • GraphQL • Microservices'],
    ]

    skills_table = Table(skills_data, colWidths=[2*inch, 4.5*inch])
    skills_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0077B5')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 0.2*inch))

    # Certifications Section
    story.append(Paragraph("Licenses & Certifications", heading_style))

    story.append(Paragraph("<b>AWS Certified Solutions Architect - Associate</b>", body_style))
    story.append(Paragraph("Amazon Web Services (AWS)", subtitle_style))
    story.append(Paragraph("Issued Jan 2022 • Credential ID: ABC123XYZ", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Certified Kubernetes Administrator (CKA)</b>", body_style))
    story.append(Paragraph("Cloud Native Computing Foundation", subtitle_style))
    story.append(Paragraph("Issued Jun 2021 • Credential ID: CKA-2021-XXXXX", body_style))
    story.append(Spacer(1, 0.2*inch))

    # Languages Section
    story.append(Paragraph("Languages", heading_style))
    lang_text = """
    <b>English</b> - Native or bilingual proficiency<br/>
    <b>Spanish</b> - Professional working proficiency<br/>
    <b>French</b> - Elementary proficiency
    """
    story.append(Paragraph(lang_text, body_style))

    # Build PDF
    doc.build(story)
    print(f"✅ Created LinkedIn template PDF at: {output_path}")


if __name__ == "__main__":
    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    output_path = os.path.join(backend_dir, "data", "linkedin_template.pdf")

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    create_linkedin_template(output_path)
    print(f"\n📄 Template generated successfully!")
    print(f"   Location: {output_path}")
    print(f"\n💡 Replace the placeholder content with your actual LinkedIn profile information.")
