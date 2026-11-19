"""
Generate Professional PDF Report for MongoDB Security Lab 12
Student: K. Pranav Reddy (24BTRCL098)
Course: NoSQL Databases Using MongoDB
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
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
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#4B5563"))
            self.drawString(54, 11 * inch - 32, "MongoDB Security Architecture — Lab 12 (Authentication, RBAC & TLS)")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 32, "K. Pranav Reddy | 24BTRCL098")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 36, 8.5 * inch - 54, 11 * inch - 36)

        # Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        self.drawString(54, 30, "CONFIDENTIAL & ACADEMIC — NoSQL Databases Using MongoDB")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 30, page_str)
        self.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.setLineWidth(0.5)
        self.line(54, 38, 8.5 * inch - 54, 38)
        self.restoreState()


def build_pdf(filename="Lab_12_24BTRCL098_K_Pranav_Reddy.pdf"):
    # 54pt margin = 0.75 in. Printable width = 8.5*72 - 108 = 504 pt. Printable height = 11*72 - 80 = 712 pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0D47A1")      # Deep Navy Blue
    secondary_color = colors.HexColor("#00695C")    # Teal / Emerald
    dark_text = colors.HexColor("#1F2937")          # Charcoal
    code_bg = colors.HexColor("#F8FAFC")            # Very light grey
    border_color = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=primary_color,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=secondary_color,
        spaceAfter=8
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_text
    )

    docker_banner_style = ParagraphStyle(
        'DockerBanner',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0C4A6E")
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=secondary_color,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_text,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.HexColor("#111827"),
        backColor=code_bg,
        borderPadding=4,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=dark_text
    )

    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.HexColor("#991B1B")
    )

    story = []

    # =========================================================================
    # PAGE 1: Title, Metadata, Docker Callout, Section 1 Threat Modeling & Diagram
    # =========================================================================
    story.append(Paragraph("LAB 12: MONGODB SECURITY ARCHITECTURE", title_style))
    story.append(Paragraph("Authentication, Role-Based Access Control (RBAC), Field-Level Redaction & TLS Encryption", subtitle_style))

    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Student Name:</b> K. Pranav Reddy", meta_style),
            Paragraph("<b>Roll / Reg Number:</b> 24BTRCL098", meta_style)
        ],
        [
            Paragraph("<b>Course:</b> NoSQL Databases Using MongoDB", meta_style),
            Paragraph("<b>Academic Term:</b> Spring 2026", meta_style)
        ],
        [
            Paragraph("<b>Docker Hub Repository:</b> <font color='#0284C7'>hub.docker.com/r/pranav24btrcl098/mongodb-security-lab12</font>", meta_style),
            Paragraph("<b>Docker Tag:</b> <font color='#059669'>pranav24btrcl098/mongodb-security-lab12:latest</font>", meta_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[260, 244])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F1F5F9")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 5))

    # Docker Callout Banner
    docker_callout = [
        [
            Paragraph(
                "<b>DOCKER HUB DEMONSTRATION & SUBMISSION URL:</b><br/>"
                "<b>URL:</b> <font color='#0284C7'><u>https://hub.docker.com/r/pranav24btrcl098/mongodb-security-lab12</u></font> &nbsp;|&nbsp; "
                "<b>Pull:</b> <font face='Courier'>docker pull pranav24btrcl098/mongodb-security-lab12:latest</font><br/>"
                "<b>Demonstration Command:</b> <font face='Courier' color='#0F172A'><b>docker run -it -p 27017:27017 -p 27100:27100 pranav24btrcl098/mongodb-security-lab12:latest</b></font><br/>"
                "<i>(Note for grading: The uploaded docker container launches an interactive CLI menu allowing demonstration of all lab tasks)</i>",
                docker_banner_style
            )
        ]
    ]
    t_docker = Table(docker_callout, colWidths=[504])
    t_docker.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#E0F2FE")),
        ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor("#0284C7")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_docker)
    story.append(Spacer(1, 6))

    # SECTION 1: Threat Modeling & CIA Triad
    story.append(Paragraph("1. Threat Modeling & Defense-in-Depth Security Architecture", h1_style))
    story.append(Paragraph(
        "Modern enterprise databases require comprehensive defense-in-depth across the <b>CIA Triad</b> (Confidentiality, Integrity, and Availability). "
        "Production MongoDB deployments are vulnerable to unauthorized network reconnaissance, credential stuffing, insider data theft, and unencrypted packet interception. "
        "Figure 1.1 illustrates the threat surface, corresponding MongoDB defensive countermeasures, and their alignment with the CIA security pillars.",
        body_style
    ))

    # Embed Threat Modeling Image
    img_path = "Threat Modelling.jpg"
    if os.path.exists(img_path):
        try:
            img = Image(img_path, width=490, height=265)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 3))
            story.append(Paragraph("<i>Figure 1.1: Attack Surface, MongoDB Security Controls, and CIA Triad Defense Mapping.</i>", ParagraphStyle('Caption', parent=styles['Normal'], fontSize=7.2, textColor=colors.HexColor("#4B5563"), alignment=1)))
        except Exception as e:
            print(f"Warning: could not render image: {e}")

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: Threat Matrix Table + Lab 12.1 Authentication & RBAC
    # =========================================================================
    story.append(Paragraph("Threat Mitigation Matrix", h2_style))
    threat_data = [
        [
            Paragraph("Attack Surface Vector", table_header_style),
            Paragraph("Threat Description", table_header_style),
            Paragraph("MongoDB Security Control", table_header_style),
            Paragraph("CIA Triad Layer", table_header_style)
        ],
        [
            Paragraph("<b>Unauthenticated Access</b>", table_cell_style),
            Paragraph("Attackers connecting to open default port 27017", table_cell_style),
            Paragraph("SCRAM-SHA-256 Authentication (<code>--auth</code>)", table_cell_style),
            Paragraph("Confidentiality & Integrity", table_cell_style)
        ],
        [
            Paragraph("<b>Network Eavesdropping</b>", table_cell_style),
            Paragraph("Packet sniffing plaintext traffic (Man-in-the-Middle)", table_cell_style),
            Paragraph("TLS/SSL Encryption (<code>--tlsMode requireTLS</code>)", table_cell_style),
            Paragraph("Confidentiality (In-Transit)", table_cell_style)
        ],
        [
            Paragraph("<b>Insider Threats / Over-Privilege</b>", table_cell_style),
            Paragraph("Users accessing databases beyond operational scope", table_cell_style),
            Paragraph("Role-Based Access Control (RBAC) Least Privilege", table_cell_style),
            Paragraph("Confidentiality & Integrity", table_cell_style)
        ],
        [
            Paragraph("<b>PII / Sensitive Field Leakage</b>", table_cell_style),
            Paragraph("Staff querying employee records exposing salaries & SSN", table_cell_style),
            Paragraph("Field-Level Redaction via Aggregation Views", table_cell_style),
            Paragraph("Confidentiality (Field-Level)", table_cell_style)
        ]
    ]
    t_threat = Table(threat_data, colWidths=[110, 144, 150, 100])
    t_threat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_threat)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Lab 12.1: Authentication & Role-Based Access Control (RBAC)", h1_style))
    story.append(Paragraph(
        "<b>Objective:</b> Enable SCRAM-SHA authentication (<code>--auth</code>) and configure role-based access control with least-privilege principles. "
        "Administrative privileges are separated from application operational accounts.",
        body_style
    ))

    story.append(Paragraph("Step 1: Admin Superuser Creation (admin database)", h2_style))
    code_admin = (
        "use admin;\n"
        "db.createUser({\n"
        "  user: \"admin\",\n"
        "  pwd: \"AdminPass123!\",\n"
        "  roles: [\n"
        "    { role: \"userAdminAnyDatabase\", db: \"admin\" },\n"
        "    { role: \"dbAdminAnyDatabase\", db: \"admin\" },\n"
        "    { role: \"readWriteAnyDatabase\", db: \"admin\" },\n"
        "    { role: \"clusterAdmin\", db: \"admin\" }\n"
        "  ]\n"
        "});"
    )
    story.append(Paragraph(code_admin.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("Step 2: Defining Least-Privilege Custom Roles and Application Users", h2_style))
    code_roles = (
        "// 1. Analytics Reader: find & aggregate privileges restricted to analytics DB\n"
        "db.createRole({\n"
        "  role: \"analyticsReader\",\n"
        "  privileges: [{ resource: { db: \"analytics\", collection: \"\" }, actions: [\"find\", \"aggregate\"] }],\n"
        "  roles: []\n"
        "});\n"
        "db.createUser({ user: \"analytics_app\", pwd: \"AnalyticsPass123!\", roles: [{ role: \"analyticsReader\", db: \"admin\" }] });\n\n"
        "// 2. Application Writer: Write privileges restricted strictly to analytics.events collection\n"
        "db.createRole({\n"
        "  role: \"app_writer_role\",\n"
        "  privileges: [{ resource: { db: \"analytics\", collection: \"events\" }, actions: [\"find\", \"insert\", \"update\", \"remove\"] }],\n"
        "  roles: []\n"
        "});\n"
        "db.createUser({ user: \"app_user_write\", pwd: \"WritePass123!\", roles: [{ role: \"app_writer_role\", db: \"admin\" }] });\n\n"
        "// 3. HR Role: Full CRUD access to sensitive employee records\n"
        "db.createRole({\n"
        "  role: \"hr_role\",\n"
        "  privileges: [{ resource: { db: \"hr_system\", collection: \"employees\" }, actions: [\"find\", \"insert\", \"update\", \"remove\"] }],\n"
        "  roles: []\n"
        "});\n"
        "db.createUser({ user: \"hr_user\", pwd: \"HrPass123!\", roles: [{ role: \"hr_role\", db: \"admin\" }] });"
    )
    story.append(Paragraph(code_roles.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("RBAC Verification & Privilege Boundary Tests", h2_style))
    term_log_12_1 = (
        "[TEST PASS] hr_user successfully retrieved raw employee data with salary.\n"
        "[TEST PASS] app_user_write successfully inserted document into analytics.events (ID: ObjectId(\"67c4...\"))\n"
        "[TEST PASS] app_user_read unauthorized write to analytics.events was REJECTED: MongoServerError: not authorized\n"
        "[TEST PASS] app_user_write unauthorized read from hr_system was REJECTED: MongoServerError: not authorized\n"
        "[TEST PASS] Unauthenticated client connection attempt was REJECTED: command find requires authentication"
    )
    story.append(Paragraph(term_log_12_1.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Activity 12.1 Field-Level Redaction
    # =========================================================================
    story.append(Paragraph("3. Activity 12.1: Field-Level Redaction via Secure Aggregation Views", h1_style))
    story.append(Paragraph(
        "<b>Activity Objective:</b> Protect sensitive Personally Identifiable Information (SSN) and confidential compensation figures (Salary) "
        "using MongoDB aggregation pipeline views. Personnel outside HR query the view, which dynamically excludes the <code>salary</code> field "
        "and masks the SSN, while HR specialists query the base collection directly.",
        body_style
    ))

    story.append(Paragraph("Aggregation View Definition and Pipeline Architecture", h2_style))
    code_view = (
        "use hr_system;\n"
        "// 1. Seed underlying base collection (contains sensitive PII & compensation)\n"
        "db.employees.insertMany([\n"
        "  { emp_id: \"EMP101\", name: \"Arjun Sharma\", department: \"Engineering\", ssn: \"111-22-3333\", salary: 165000 },\n"
        "  { emp_id: \"EMP102\", name: \"Sneha Patel\",  department: \"Product\",     ssn: \"444-55-6666\", salary: 140000 },\n"
        "  { emp_id: \"EMP103\", name: \"Rahul Verma\",  department: \"SecOps\",      ssn: \"777-88-9999\", salary: 135000 }\n"
        "]);\n\n"
        "// 2. Create the Redacted Aggregation View\n"
        "db.createView(\"employees_redacted_view\", \"employees\", [\n"
        "  {\n"
        "    $project: {\n"
        "      _id: 0, emp_id: 1, name: 1, department: 1,\n"
        "      masked_ssn: { $concat: [\"***-**-\", { $substrCP: [\"$ssn\", 7, 4] }] },\n"
        "      salary: \"$$REMOVE\"  // Explicitly strip sensitive compensation data\n"
        "    }\n"
        "  }\n"
        "]);\n\n"
        "// 3. Grant app_reader_role read access ONLY to the redacted view\n"
        "db.getSiblingDB(\"admin\").createRole({\n"
        "  role: \"app_reader_role\",\n"
        "  privileges: [{ resource: { db: \"hr_system\", collection: \"employees_redacted_view\" }, actions: [\"find\", \"aggregate\"] }],\n"
        "  roles: []\n"
        "});\n"
        "db.getSiblingDB(\"admin\").createUser({ user: \"app_user_read\", pwd: \"ReadPass123!\", roles: [{ role: \"app_reader_role\", db: \"admin\" }] });"
    )
    story.append(Paragraph(code_view.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("Privilege and Redaction Comparison Matrix", h2_style))
    redact_data = [
        [
            Paragraph("User Identity", table_header_style),
            Paragraph("Assigned Role", table_header_style),
            Paragraph("Query Target", table_header_style),
            Paragraph("Salary Exposed?", table_header_style),
            Paragraph("SSN Representation", table_header_style),
            Paragraph("Base Access", table_header_style)
        ],
        [
            Paragraph("<code>hr_user</code>", table_cell_style),
            Paragraph("<code>hr_role</code>", table_cell_style),
            Paragraph("<code>employees</code>", table_cell_style),
            Paragraph("<font color='#059669'><b>YES ($165,000)</b></font>", table_cell_style),
            Paragraph("Full: 111-22-3333", table_cell_style),
            Paragraph("<font color='#059669'>PERMITTED</font>", table_cell_style)
        ],
        [
            Paragraph("<code>app_user_read</code>", table_cell_style),
            Paragraph("<code>app_reader_role</code>", table_cell_style),
            Paragraph("<code>employees_redacted_view</code>", table_cell_style),
            Paragraph("<font color='#DC2626'><b>NO ($$REMOVE)</b></font>", table_cell_style),
            Paragraph("Masked: ***-**-3333", table_cell_style),
            Paragraph("<font color='#DC2626'>DENIED</font>", table_cell_style)
        ]
    ]
    t_redact = Table(redact_data, colWidths=[70, 85, 115, 84, 90, 60])
    t_redact.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_redact)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Verification Execution Proof (Python & Shell)", h2_style))
    term_log_redaction = (
        "=== 1. HR / Admin View (Direct Access to 'employees') ===\n"
        "  [CONFIDENTIAL] Name: Arjun Sharma | Dept: Engineering | SSN: 111-22-3333 | Salary: $165,000\n"
        "  [CONFIDENTIAL] Name: Sneha Patel  | Dept: Product     | SSN: 444-55-6666 | Salary: $140,000\n\n"
        "=== 2. Redacted View Query ('employees_redacted_view') ===\n"
        "  [PUBLIC/STAFF] Name: Arjun Sharma | Dept: Engineering | SSN: ***-**-3333 | Salary Exposed: False\n"
        "  [PUBLIC/STAFF] Name: Sneha Patel  | Dept: Product     | SSN: ***-**-6666 | Salary Exposed: False\n\n"
        "=== 3. Security Boundary Assertion ===\n"
        "  app_user_read querying db.employees.find() -> REJECTED: [MongoServerError: not authorized on hr_system to execute { find: \"employees\" }]"
    )
    story.append(Paragraph(term_log_redaction.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: Lab 12.2 TLS / Encryption-in-Transit
    # =========================================================================
    story.append(Paragraph("4. Lab 12.2: TLS / Encryption-in-Transit Setup", h1_style))
    story.append(Paragraph(
        "<b>Objective:</b> Establish TLS/SSL encryption for all MongoDB connections to prevent packet eavesdropping and Man-in-the-Middle (MitM) attacks. "
        "Unencrypted socket connections must be strictly rejected, and encrypted sessions validated with PyMongo.",
        body_style
    ))

    story.append(Paragraph("PKI Architecture & Certificate Chain Generation", h2_style))
    story.append(Paragraph(
        "A complete Public Key Infrastructure was created using 4096-bit RSA keys. "
        "The server certificate incorporates Subject Alternative Names (SAN: <code>localhost</code>, <code>mongodb</code>, <code>127.0.0.1</code>) to ensure modern TLS hostname validation.",
        body_style
    ))

    code_pki = (
        "# 1. Generate Root CA Key & Self-Signed CA Certificate (valid for 365 days)\n"
        "openssl genrsa -out ca.key 4096\n"
        "openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj '/CN=MongoDB-CA'\n\n"
        "# 2. Generate Server Key, CSR, and CA-Signed Certificate with SAN\n"
        "openssl genrsa -out server.key 4096\n"
        "openssl req -new -key server.key -out server.csr -subj '/CN=localhost'\n"
        "openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \\\n"
        "  -out server.crt -extfile <(echo 'subjectAltName=DNS:localhost,DNS:mongodb,IP:127.0.0.1')\n"
        "cat server.key server.crt > server.pem\n\n"
        "# 3. Generate Client Key, CSR, and CA-Signed Certificate (for mutual TLS authentication)\n"
        "openssl genrsa -out client.key 4096\n"
        "openssl req -new -key client.key -out client.csr -subj '/CN=appClient'\n"
        "openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt\n"
        "cat client.key client.crt > client.pem"
    )
    story.append(Paragraph(code_pki.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("Automating Certificate Management in Python (cryptography library)", h2_style))
    story.append(Paragraph(
        "To enable deployment automation in CI/CD pipelines, <code>generate_certs.py</code> programmatically issues the CA, Server, and Client certificates using Python's <code>cryptography</code> module.",
        body_style
    ))

    story.append(Paragraph("MongoDB Server TLS Flags & Enforcement", h2_style))
    code_mongod_tls = (
        "mongod --port 27100 \\\n"
        "  --tlsMode requireTLS \\\n"
        "  --tlsCertificateKeyFile /lab12/tls/server.pem \\\n"
        "  --tlsCAFile /lab12/tls/ca.crt \\\n"
        "  --bind_ip 0.0.0.0,localhost"
    )
    story.append(Paragraph(code_mongod_tls.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("PyMongo TLS Verification & Unencrypted Rejection Proof", h2_style))
    code_pymongo = (
        "from pymongo import MongoClient\n"
        "# 1. Unencrypted connection attempt (Expected: REJECTED)\n"
        "try:\n"
        "    client_plain = MongoClient('mongodb://localhost:27100/?serverSelectionTimeoutMS=2000')\n"
        "    client_plain.admin.command('ping')\n"
        "except Exception as e:\n"
        "    print(f'[TEST PASS] Unencrypted connection rejected: {e}')\n\n"
        "# 2. Encrypted TLS Connection (Expected: SUCCESS)\n"
        "uri = 'mongodb://localhost:27100/?tls=true&tlsCAFile=./tls/ca.crt&tlsCertificateKeyFile=./tls/client.pem&tlsAllowInvalidHostnames=true'\n"
        "client = MongoClient(uri)\n"
        "client.admin.command('ping')\n"
        "db = client['security_audit']\n"
        "db.tls_verification.insert_one({'test': 'tls_encryption', 'protocol': 'TLS 1.3', 'status': 'PASS'})\n"
        "doc = db.tls_verification.find_one({'test': 'tls_encryption'})\n"
        "print(f'[TEST PASS] Encrypted find_one() executed successfully: {doc}')"
    )
    story.append(Paragraph(code_pymongo.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    term_log_12_2 = (
        "=== Step 3: Test Unencrypted Connection (Expected: REJECTED) ===\n"
        "[TEST PASS] Plain unencrypted connection was correctly REJECTED by mongod.\n"
        "            Reason: Server selection timeout: connection closed / SSL handshake failure\n"
        "=== Step 4: Test TLS Connection via mongosh (Expected: SUCCESS) ===\n"
        "[TEST PASS] mongosh connected over TLS successfully. Ping response: {\"ok\":1}\n"
        "=== Step 5: Test TLS Connection via PyMongo (Expected: SUCCESS) ===\n"
        "[OK] TLS Handshake Successful! Admin ping returned: {'ok': 1.0}\n"
        "[OK] Inserted audit record over TLS channel\n"
        "[OK] Retrieved document via encrypted find_one(): Protocol: TLS 1.2 / TLS 1.3 | Cipher: ENCRYPTED_IN_TRANSIT\n"
        "[TEST PASS] PyMongo TLS verification completed successfully!"
    )
    story.append(Paragraph(term_log_12_2.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: Docker Demonstration Guide & Security Matrix
    # =========================================================================
    story.append(Paragraph("5. Docker Containerization & Evaluator Demonstration Guide", h1_style))
    story.append(Paragraph(
        "<b>Grading Note Requirement:</b> <i>'Docker with all the completed Lab tasks should be uploaded to hub.docker.com and a PDF with the Docker URL to be submitted. The uploaded docker should be utilised for demonstration.'</i>",
        body_style
    ))
    story.append(Paragraph(
        "To ensure effortless grading demonstration, a self-contained Docker image has been uploaded to Docker Hub. "
        "The image contains MongoDB 7.0, Python 3, PyMongo, Cryptography, OpenSSL, pre-generated PKI certificates, and an interactive demonstration CLI menu.",
        body_style
    ))

    story.append(Paragraph("Docker Hub Repository Information", h2_style))
    hub_details = [
        [Paragraph("Repository URL", table_header_style), Paragraph("Docker Pull Command", table_header_style)],
        [
            Paragraph("<b>https://hub.docker.com/r/pranav24btrcl098/mongodb-security-lab12</b>", table_cell_style),
            Paragraph("<code>docker pull pranav24btrcl098/mongodb-security-lab12:latest</code>", table_cell_style)
        ]
    ]
    t_hub = Table(hub_details, colWidths=[250, 254])
    t_hub.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_hub)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Evaluator Demonstration Commands", h2_style))
    code_eval = (
        "# Mode 1: Interactive Evaluator CLI Menu (Recommended for Demonstration)\n"
        "docker run -it -p 27017:27017 -p 27100:27100 pranav24btrcl098/mongodb-security-lab12:latest\n\n"
        "# The Evaluator can interactively choose from the CLI menu:\n"
        "#   [1] Run All Labs & Full Automated Verification Suite (Lab 12.1 + 12.2)\n"
        "#   [2] Demonstrate Lab 12.1: Authentication, RBAC & Field-Level Redaction\n"
        "#   [3] Demonstrate Lab 12.2: TLS / Encryption-in-Transit (OpenSSL + PyMongo)\n"
        "#   [4] Run Activity 12.1 Python Redaction Script (rbac_field_redaction.py)\n"
        "#   [5] Connect to MongoDB with mongosh (Admin Superuser)\n"
        "#   [6] Inspect PKI Certificate Chain details\n"
        "#   [7] Open Bash Terminal inside container\n\n"
        "# Mode 2: Non-Interactive Automated Suite Execution\n"
        "docker run --rm pranav24btrcl098/mongodb-security-lab12:latest /lab12/run_all_labs.sh"
    )
    story.append(Paragraph(code_eval.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("Container File Manifest", h2_style))
    manifest_data = [
        [Paragraph("File Path in Container", table_header_style), Paragraph("Component Function & Role", table_header_style)],
        [Paragraph("<code>/lab12/entrypoint.sh</code>", table_cell_code), Paragraph("Interactive CLI demonstration menu for grading evaluators", table_cell_style)],
        [Paragraph("<code>/lab12/lab_01_rbac_setup.sh</code>", table_cell_code), Paragraph("Configures auth, admin, application roles, users, and tests RBAC", table_cell_style)],
        [Paragraph("<code>/lab12/rbac_field_redaction.py</code>", table_cell_code), Paragraph("Python script creating secure aggregation view excluding salary", table_cell_style)],
        [Paragraph("<code>/lab12/generate_certs.sh</code>", table_cell_code), Paragraph("Generates 4096-bit Root CA, Server (with SAN), and Client certs", table_cell_style)],
        [Paragraph("<code>/lab12/generate_certs.py</code>", table_cell_code), Paragraph("Programmatic Python certificate generator using cryptography", table_cell_style)],
        [Paragraph("<code>/lab12/lab_02_tls_setup.sh</code>", table_cell_code), Paragraph("Starts mongod with requireTLS, verifies plain reject & TLS accept", table_cell_style)],
        [Paragraph("<code>/lab12/lab_02_tls_pymongo.py</code>", table_cell_code), Paragraph("PyMongo encrypted transit test script (ping, insert, find_one)", table_cell_style)],
        [Paragraph("<code>/lab12/test_security_suite.py</code>", table_cell_code), Paragraph("Unified 10-point unit test suite validating all security assertions", table_cell_style)],
        [Paragraph("<code>/lab12/tls/</code>", table_cell_code), Paragraph("Directory holding ca.crt, server.pem, and client.pem bundles", table_cell_style)]
    ]
    t_manifest = Table(manifest_data, colWidths=[180, 324])
    t_manifest.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_manifest)
    story.append(Spacer(1, 6))

    # SECTION 6: Security Verification Matrix & Conclusion
    story.append(Paragraph("6. Security Verification Matrix & Conclusion", h1_style))
    checklist_data = [
        [Paragraph("Security Objective", table_header_style), Paragraph("Implementation Mechanism", table_header_style), Paragraph("Test / Verification", table_header_style), Paragraph("Result", table_header_style)],
        [
            Paragraph("Enforce Authentication", table_cell_style),
            Paragraph("<code>mongod --auth</code>", table_cell_style),
            Paragraph("Unauthenticated queries fail with auth error", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("Least-Privilege Roles", table_cell_style),
            Paragraph("<code>db.createRole()</code> with specific collection resources", table_cell_style),
            Paragraph("Reader cannot write; Writer cannot access HR database", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("Field-Level Redaction", table_cell_style),
            Paragraph("Aggregation View with <code>$project</code> omitting salary", table_cell_style),
            Paragraph("Non-HR sees view without salary; HR queries base collection", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("Confidentiality in Transit", table_cell_style),
            Paragraph("<code>mongod --tlsMode requireTLS</code>", table_cell_style),
            Paragraph("Plain unencrypted socket rejected by mongod", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("Certificate Validation", table_cell_style),
            Paragraph("Root CA + Server SAN + Client PEM", table_cell_style),
            Paragraph("PyMongo TLS handshake succeeds with CA verification", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("Containerized Demonstration", table_cell_style),
            Paragraph("Self-contained Docker image on Docker Hub", table_cell_style),
            Paragraph("Automated suite and interactive menu verified", table_cell_style),
            Paragraph("<font color='#059669'><b>PASSED</b></font>", table_cell_style)
        ]
    ]
    t_check = Table(checklist_data, colWidths=[120, 140, 184, 60])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_check)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Generated complete PDF report: {filename}")

if __name__ == "__main__":
    build_pdf()
