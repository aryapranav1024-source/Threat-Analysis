import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner margins (padding) for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_table_borders(table, color="D0D7DE", sz="4", val="single"):
    """Apply neat borders to a table."""
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:left w:val="none"/>
                <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:right w:val="none"/>
                <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)

def add_callout(doc, title, text, border_color="1B365D", bg_color="F4F6F9"):
    """Add a shaded callout box with a colored left accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"📌 {title}\n")
    run_t.bold = True
    run_t.font.name = "Arial"
    run_t.font.size = Pt(10.5)
    run_t.font.color.rgb = RGBColor.from_string(border_color)
    
    run_b = p.add_run(text)
    run_b.font.name = "Arial"
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text):
    """Add a monospace formatted code/terminal output block."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "282C34")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="3E4451"/>
            <w:left w:val="single" w:sz="4" w:space="0" w:color="3E4451"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="3E4451"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="3E4451"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0xAB, 0xB2, 0xBF)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_report():
    doc = docx.Document()
    
    # Page Margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)
        
        # Header / Footer
        header = sec.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("NoSQL Lab 15: Multi-Tenant Architecture & Data Migration | MongoDB")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        
        footer = sec.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Confidential — For Academic & Technical Evaluation Only")
        frun.font.name = "Arial"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    # Document Title Block
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    t_run = title_p.add_run("MongoDB Multi-Tenant SaaS Architecture & Data Migration")
    t_run.bold = True
    t_run.font.name = "Arial"
    t_run.font.size = Pt(22)
    t_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Navy

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(14)
    s_run = sub_p.add_run("Comprehensive Technical Report on Shared-Collection Isolation, Rate Limiting, and Idempotent Tenant Migration")
    s_run.font.name = "Arial"
    s_run.font.size = Pt(12)
    s_run.font.color.rgb = RGBColor(0x4B, 0x6B, 0x94)

    # Metadata Table
    meta_table = doc.add_table(rows=2, cols=4)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    col_widths = [Inches(1.5), Inches(1.8), Inches(1.4), Inches(1.8)]
    for row in meta_table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    meta_data = [
        [("Course / Lab: ", "NoSQL Lab 15"), ("Database: ", "MongoDB (Local Replica / Standalone)")],
        [("Scripts Evaluated: ", "lab_01_multitenant_api.py, lab_02_tenant_migration.py"), ("Execution Status: ", "Verified & Fully Tested (100% Pass)")]
    ]

    for r_idx, row in enumerate(meta_data):
        for c_idx, (label, val) in enumerate(row):
            cell = meta_table.cell(r_idx, c_idx * 2)
            cell_val = meta_table.cell(r_idx, c_idx * 2 + 1)
            set_cell_background(cell, "F4F6F9")
            set_cell_background(cell_val, "F4F6F9")
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            set_cell_margins(cell_val, top=60, bottom=60, left=80, right=80)
            
            p1 = cell.paragraphs[0]
            p1.paragraph_format.space_before = Pt(0)
            p1.paragraph_format.space_after = Pt(0)
            r1 = p1.add_run(label)
            r1.bold = True
            r1.font.name = "Arial"
            r1.font.size = Pt(9)
            r1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            
            p2 = cell_val.paragraphs[0]
            p2.paragraph_format.space_before = Pt(0)
            p2.paragraph_format.space_after = Pt(0)
            r2 = p2.add_run(val)
            r2.font.name = "Arial"
            r2.font.size = Pt(9)
            r2.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    set_table_borders(meta_table, color="D0D7DE", sz="4")
    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # 1. Executive Summary
    h1 = doc.add_heading("1. Executive Summary", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)
    for r in h1.runs:
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_exec = doc.add_paragraph(
        "Modern Software-as-a-Service (SaaS) applications require robust multi-tenancy models that balance "
        "cost-efficiency, performance, and tenant data isolation. This report presents an in-depth examination and "
        "experimental verification of multi-tenant engineering in MongoDB through two distinct laboratory exercises:\n\n"
        "1. Activity 1 (lab_01_multitenant_api.py): Implements a shared-collection multi-tenant task API. It explores "
        "the operational risks of tenant isolation, highlighting how a missing tenant scoping filter creates critical "
        "Insecure Direct Object Reference (IDOR) vulnerabilities. Additionally, it verifies a native MongoDB rolling "
        "window rate limiter.\n"
        "2. Activity 2 (lab_02_tenant_migration.py): Simulates tenant isolation tier upgrades, migrating an enterprise "
        "tenant (tenant-acme) from the shared collection into an isolated database (database-per-tenant). The migration "
        "engine provides dry-run preview, non-destructive copying, idempotent upsert execution, cryptographic SHA-256 "
        "data verification, and safe rollback capabilities."
    )
    p_exec.paragraph_format.line_spacing = 1.15
    p_exec.paragraph_format.space_after = Pt(10)

    # 2. Activity 1: Design a Multi-Tenant API
    h2 = doc.add_heading("2. Activity 1: Design a Multi-Tenant API (lab_01_multitenant_api.py)", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    for r in h2.runs:
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_a1_intro = doc.add_paragraph(
        "Shared-collection multi-tenancy stores documents from all tenants inside a single collection "
        "(saas_app.tasks), using a discriminator field (`tenant_id`). While this minimizes infrastructure overhead "
        "and database connection costs, it places the entire responsibility of boundary enforcement on application code. "
        "MongoDB itself has no inherent understanding of tenant ownership; therefore, query filters are the sole line of defense."
    )
    p_a1_intro.paragraph_format.line_spacing = 1.15

    # Crucial Task Question 1 Callout
    q1_text = (
        "Question Prompt: Write down what would go wrong -- concretely, with an example -- if update_task's filter only "
        "checked {'_id': task_id} without also checking tenant_id. Then confirm that scenario is exactly what the actual "
        "filter prevents.\n\n"
        "Detailed Failure Analysis:\n"
        "• Root Cause: In a shared collection, ObjectIds are globally unique across the collection but not secret. If an update "
        "operation filters exclusively on {'_id': task_id}, any caller who possesses or correctly guesses a valid ObjectId can "
        "modify that document regardless of the tenant making the API call. This is a severe Insecure Direct Object Reference (IDOR) vulnerability.\n\n"
        "• Concrete Example:\n"
        "  1. Tenant Acme creates a sensitive task: {_id: ObjectId('6736fc...'), tenant_id: 'tenant-acme', title: 'Setup ML Pipeline', status: 'open'}.\n"
        "  2. An attacker or unauthorized user from Tenant Globex issues an update request specifying task_id='6736fc...' with updates: {'status': 'deleted'} or altering task details.\n"
        "  3. If update_task ran: col.update_one({'_id': task_id}, {'$set': updates}), MongoDB would locate the document by ObjectId alone and apply Globex's changes directly to Acme's data.\n"
        "  4. Consequence: Tenant Globex modifies or corrupts Tenant Acme's private operational data, violating tenant confidentiality and integrity guarantees.\n\n"
        "• Confirmation of Actual Prevention:\n"
        "In lab_01_multitenant_api.py, line 46 implements the compound filter:\n"
        "    col.update_one({'_id': task_id, 'tenant_id': tenant_id}, {'$set': updates})\n"
        "When Globex attempts to update Acme's task ID using tenant_id='tenant-globex', MongoDB searches for a document satisfying BOTH conditions. "
        "Because Acme's document has tenant_id='tenant-acme', the query matches zero documents (matched_count = 0, modified_count = 0). "
        "The function returns False, completely blocking the cross-tenant modification."
    )
    add_callout(doc, "CRITICAL SECURITY ANALYSIS: Filter Scoping & Cross-Tenant Vulnerability", q1_text, border_color="1B365D", bg_color="F4F6F9")

    # API Function Breakdown
    h3_ops = doc.add_heading("2.1 Core API Functions & Implementation Architecture", level=2)
    h3_ops.paragraph_format.space_before = Pt(10)
    h3_ops.paragraph_format.space_after = Pt(4)
    for r in h3_ops.runs:
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)

    p_ops = doc.add_paragraph(
        "The task-management API is constructed with four core functions:\n"
        "1. create_task(col, tenant_id, title, description, priority, assignee): Injects the mandatory tenant_id field, "
        "initializes operational state (status='open'), and attaches Unix timestamps (created_at, updated_at).\n"
        "2. get_tasks(col, tenant_id, status=None, priority=None): Queries tasks with mandatory scoping: {'tenant_id': tenant_id}. "
        "Optional query filters for status and priority are dynamically attached, and projection limits fields to prevent data leaks.\n"
        "3. update_task(col, tenant_id, task_id, updates): Updates task metadata while enforcing the compound filter "
        "{'_id': task_id, 'tenant_id': tenant_id}. It updates the 'updated_at' timestamp and returns a boolean indicating modification success.\n"
        "4. check_rate_limit(rate_col, tenant_id, limit=10, window_secs=60): A database-native rolling-window rate limiter. "
        "It queries the rate_limits collection for entries within (current_time - window_secs) belonging to tenant_id. "
        "If count >= limit, the request is rejected (returns False); otherwise, a new timestamp record is inserted and the request is permitted."
    )
    p_ops.paragraph_format.line_spacing = 1.15

    # Execution Logs for Activity 1
    h3_logs = doc.add_heading("2.2 Activity 1 Execution Results & Verification", level=2)
    h3_logs.paragraph_format.space_before = Pt(10)
    h3_logs.paragraph_format.space_after = Pt(4)
    for r in h3_logs.runs:
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)

    p_log_intro = doc.add_paragraph(
        "Executing `python lab_01_multitenant_api.py` produced the following verified output, demonstrating successful "
        "task creation, tenant isolation during reads, permitted same-tenant updates, blocked cross-tenant updates, and rate limiting:"
    )
    p_log_intro.paragraph_format.space_after = Pt(4)

    act1_log = (
        "======================================================================\n"
        "  Lab 15.1: Multi-Tenant SaaS API\n"
        "======================================================================\n"
        "=== Creating Tasks ===\n"
        "  Created 4 tasks across 2 tenants.\n\n"
        "=== tenant-acme Tasks ===\n"
        "  [high  ] Setup ML Pipeline              (open) -> arjun\n"
        "  [medium] Data Validation                (open) -> sneha\n\n"
        "=== tenant-globex Tasks ===\n"
        "  [high  ] API Integration                (open) -> rahul\n"
        "  [low   ] User Testing                   (open) -> None\n\n"
        "=== Update: Close ML Pipeline task ===\n"
        "  Update success: True\n\n"
        "=== Cross-Tenant Access Attempt (should fail) ===\n"
        "  Globex trying to update Acme's task: False (False = blocked!)\n\n"
        "=== Rate Limiting (10 req/60s) ===\n"
        "  Request  1: ALLOWED\n"
        "  Request  2: ALLOWED\n"
        "  Request  3: ALLOWED\n"
        "  Request  4: ALLOWED\n"
        "  Request  5: ALLOWED\n"
        "  Request  6: ALLOWED\n"
        "  Request  7: ALLOWED\n"
        "  Request  8: ALLOWED\n"
        "  Request  9: ALLOWED\n"
        "  Request 10: ALLOWED\n"
        "  Request 11: RATE LIMITED\n"
        "  Request 12: RATE LIMITED\n\n"
        "======================================================================\n"
        "  Lab 15.1 Complete\n"
        "======================================================================"
    )
    add_code_block(doc, act1_log)

    # Multi-Tenant Architecture Comparison Table
    h3_arch = doc.add_heading("2.3 Multi-Tenant Architectural Strategies Comparison", level=2)
    h3_arch.paragraph_format.space_before = Pt(10)
    h3_arch.paragraph_format.space_after = Pt(4)
    for r in h3_arch.runs:
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)

    p_arch_intro = doc.add_paragraph(
        "SaaS systems typically adopt one of three isolation tiers depending on security requirements, compliance mandates, "
        "and operational budgets:"
    )
    p_arch_intro.paragraph_format.space_after = Pt(6)

    comp_table = doc.add_table(rows=4, cols=4)
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    comp_table.autofit = False
    arch_widths = [Inches(1.5), Inches(1.1), Inches(1.9), Inches(2.0)]
    for row in comp_table.rows:
        for i, w in enumerate(arch_widths):
            row.cells[i].width = w

    headers = ["Approach", "Isolation", "Pros & Benefits", "Cons & Trade-offs"]
    for i, h in enumerate(headers):
        cell = comp_table.cell(0, i)
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    rows_data = [
        ("Document tenant_id\n(Shared Collection)", "Medium\n(Logical)", "Cheapest infrastructure cost; single collection and shared indexes; simplest to provision.", "Application code must explicitly filter on tenant_id; risk of catastrophic cross-tenant data leaks (IDOR); noisy neighbor issues."),
        ("Collection-per-tenant", "Strong\n(Schema)", "Straightforward namespace RBAC; simpler per-tenant backup/restore; no need for tenant_id filter inside collection.", "MongoDB index and namespace limits at scale; higher RAM footprint for open wiredTiger collections; migration overhead."),
        ("Database-per-tenant", "Strongest\n(Physical)", "Complete physical and cryptographic isolation; dedicated database-level encryption keys; zero cross-tenant risk; compliance-ready (HIPAA, SOC2).", "Highest resource overhead; connection pooling fragmentation; complex cross-tenant aggregation; operational complexity at scale.")
    ]

    for r_idx, (app, iso, pros, cons) in enumerate(rows_data, start=1):
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, text in enumerate([app, iso, pros, cons]):
            cell = comp_table.cell(r_idx, c_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    set_table_borders(comp_table, color="D0D7DE", sz="4")
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 3. Activity 2: Data Migration Between Tenant Isolation Strategies
    h2_mig = doc.add_heading("3. Activity 2: Data Migration Between Isolation Strategies (lab_02_tenant_migration.py)", level=1)
    h2_mig.paragraph_format.space_before = Pt(14)
    h2_mig.paragraph_format.space_after = Pt(6)
    for r in h2_mig.runs:
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_mig_intro = doc.add_paragraph(
        "As SaaS customers expand, enterprise clients frequently mandate strict database-per-tenant isolation for compliance "
        "(e.g., SOC 2 Type II, ISO 27001, HIPAA). Real-world architectures must support transitioning specific tenants out of the "
        "shared collection into dedicated databases without interrupting service for other tenants or re-architecting the entire platform."
    )
    p_mig_intro.paragraph_format.line_spacing = 1.15

    # Crucial Task Question 2 Callout
    q2_text = (
        "Question Prompt: Before running the second (repeat) migration: predict whether the tenant's document count in the "
        "new database will double, stay the same, or something else. Then run it and confirm against the printed target_count.\n\n"
        "Detailed Theoretical Prediction:\n"
        "• Prediction: The document count in the target database will stay EXACTLY THE SAME (2 documents).\n\n"
        "• Technical Justification & Engineering Mechanism:\n"
        "  1. Naive Migration Flaw: If a migration uses blind insertions (col.insert_one / col.insert_many), running the script twice "
        "or resuming after a mid-flight network crash will generate duplicate records because MongoDB will automatically generate new "
        "unique ObjectId values for each inserted document. The count would double from 2 to 4.\n"
        "  2. Idempotent Upsert Pattern: lab_02_tenant_migration.py avoids this pitfall by utilizing an idempotent update_one call "
        "with upsert=True keyed on a natural compound identifier (lines 82-86):\n"
        "         target_col.update_one(\n"
        "             {'tenant_id': doc['tenant_id'], 'title': doc['title']},\n"
        "             {'$set': doc},\n"
        "             upsert=True\n"
        "         )\n"
        "  3. End-State Convergence: When the script executes the second time, MongoDB queries target_col for existing records matching "
        "{'tenant_id': 'tenant-acme', 'title': <title>}. Because both records already exist from Run 1, update_one matches the existing "
        "documents and simply overwrites their fields with $set. Zero new documents are inserted.\n\n"
        "• Empirical Confirmation Against Execution Results:\n"
        "  - Run 1 (Initial Migration): Source Count = 2, Target Count = 2, Status = MIGRATED.\n"
        "  - Run 2 (Repeat Migration): Source Count = 2, Target Count = 2, Status = MIGRATED.\n"
        "  - Output Log Confirmation: '  [OK] Re-running did not create duplicates -- migration is idempotent.'"
    )
    add_callout(doc, "CRITICAL MIGRATION PREDICTION & IDEMPOTENCY CONFIRMATION", q2_text, border_color="28A745", bg_color="F4F6F9")

    # Migration Design Principles
    h3_principles = doc.add_heading("3.1 Key Migration Architectural Principles", level=2)
    h3_principles.paragraph_format.space_before = Pt(10)
    h3_principles.paragraph_format.space_after = Pt(4)
    for r in h3_principles.runs:
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)

    p_prin = doc.add_paragraph(
        "The migration script embodies four vital production-grade migration patterns:\n"
        "1. Dry-Run Verification (`--dry-run`): Performs a zero-write simulation. It connects to the shared collection, "
        "counts the documents matching `tenant_id`, and reports the planned target database name (`tenant_acme`). This allows operators "
        "to validate batch sizes and configurations prior to execution.\n"
        "2. Idempotent Data Movement: By upserting on natural compound business keys `(tenant_id, title)`, the operation can be "
        "retried indefinitely without data corruption or document duplication.\n"
        "3. Cryptographic Verification (`content_checksum`): Document count parity alone is insufficient to guarantee migration "
        "integrity. The script computes a deterministic SHA-256 hash of all documents sorted by title (`content_checksum`). "
        "Migration is marked `MIGRATED` only if both `len(target_docs) == len(source_docs)` AND `source_checksum == target_checksum`.\n"
        "4. Non-Destructive Copy & Rollback Path (`--rollback`): The script copies data into the new database without deleting from "
        "the shared collection. If validation fails or the deployment is aborted, rollback simply drops the dedicated database "
        "(`client.drop_database('tenant_acme')`). The original shared data remains untouched, preventing data loss."
    )
    p_prin.paragraph_format.line_spacing = 1.15

    # Execution Logs for Activity 2
    h3_mig_logs = doc.add_heading("3.2 Activity 2 Execution Verification & Output Logs", level=2)
    h3_mig_logs.paragraph_format.space_before = Pt(10)
    h3_mig_logs.paragraph_format.space_after = Pt(4)
    for r in h3_mig_logs.runs:
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)

    # 1. Dry Run
    p_dry_title = doc.add_paragraph("A. Dry Run Execution (`python lab_02_tenant_migration.py --dry-run`):")
    p_dry_title.paragraph_format.space_before = Pt(4)
    p_dry_title.paragraph_format.space_after = Pt(2)
    p_dry_title.runs[0].bold = True

    dry_log = (
        "======================================================================\n"
        "  Lab 15.2: Data Migration Between Tenant Isolation Strategies\n"
        "======================================================================\n"
        "=== Step 1: Seed shared-collection baseline (from Lab 15.1) ===\n"
        "  [OK] Seeded shared collection 'saas_app.tasks' for tenant-acme and tenant-globex.\n\n"
        "=== Step 2: Migrate 'tenant-acme' (DRY RUN) ===\n"
        "                      Tenant Migration Summary                       \n"
        "+-------------+---------+-------------+--------------+--------------+\n"
        "| Tenant      | Status  | Target DB   | Source Count | Target Count |\n"
        "+-------------+---------+-------------+--------------+--------------+\n"
        "| tenant-acme | DRY_RUN | tenant_acme |            2 |            - |\n"
        "+-------------+---------+-------------+--------------+--------------+\n\n"
        "======================================================================\n"
        "  Lab 15.2 Complete\n"
        "======================================================================\n"
    )
    add_code_block(doc, dry_log)

    # 2. Live Migration & Idempotency Run
    p_live_title = doc.add_paragraph("B. Live Migration & Idempotency Re-run Execution (`python lab_02_tenant_migration.py`):")
    p_live_title.paragraph_format.space_before = Pt(6)
    p_live_title.paragraph_format.space_after = Pt(2)
    p_live_title.runs[0].bold = True

    live_log = (
        "======================================================================\n"
        "  Lab 15.2: Data Migration Between Tenant Isolation Strategies\n"
        "======================================================================\n"
        "=== Step 1: Seed shared-collection baseline (from Lab 15.1) ===\n"
        "  [OK] Seeded shared collection 'saas_app.tasks' for tenant-acme and tenant-globex.\n\n"
        "=== Step 2: Migrate 'tenant-acme' (LIVE) ===\n"
        "                       Tenant Migration Summary                       \n"
        "+-------------+----------+-------------+--------------+--------------+\n"
        "| Tenant      | Status   | Target DB   | Source Count | Target Count |\n"
        "+-------------+----------+-------------+--------------+--------------+\n"
        "| tenant-acme | MIGRATED | tenant_acme |            2 |            2 |\n"
        "+-------------+----------+-------------+--------------+--------------+\n\n"
        "=== Step 3: Re-run migration to prove it's idempotent ===\n"
        "                       Tenant Migration Summary                       \n"
        "+-------------+----------+-------------+--------------+--------------+\n"
        "| Tenant      | Status   | Target DB   | Source Count | Target Count |\n"
        "+-------------+----------+-------------+--------------+--------------+\n"
        "| tenant-acme | MIGRATED | tenant_acme |            2 |            2 |\n"
        "+-------------+----------+-------------+--------------+--------------+\n"
        "  [OK] Re-running did not create duplicates -- migration is idempotent.\n\n"
        "  Shared collection still has the original documents (migration copies, it doesn't move-and-delete, until you\n"
        "  explicitly clean up the source after confirming the new tier is stable).\n\n"
        "  To undo this migration: python chapter-15/lab_02_tenant_migration.py --tenant tenant-acme --rollback\n\n"
        "======================================================================\n"
        "  Lab 15.2 Complete\n"
        "======================================================================\n"
    )
    add_code_block(doc, live_log)

    # 3. Rollback Run
    p_roll_title = doc.add_paragraph("C. Rollback Execution (`python lab_02_tenant_migration.py --rollback`):")
    p_roll_title.paragraph_format.space_before = Pt(6)
    p_roll_title.paragraph_format.space_after = Pt(2)
    p_roll_title.runs[0].bold = True

    roll_log = (
        "======================================================================\n"
        "  Lab 15.2: Data Migration Between Tenant Isolation Strategies\n"
        "======================================================================\n"
        "=== Step 1: Seed shared-collection baseline (from Lab 15.1) ===\n"
        "  [OK] Seeded shared collection 'saas_app.tasks' for tenant-acme and tenant-globex.\n\n"
        "=== Rolling back migration for tenant-acme ===\n"
        "  [OK] Dropped database 'tenant_acme'. Shared collection is untouched.\n\n"
        "======================================================================\n"
        "  Lab 15.2 Complete (rollback)\n"
        "======================================================================\n"
    )
    add_code_block(doc, roll_log)

    # 4. Production Engineering Recommendations
    h2_rec = doc.add_heading("4. Production Best Practices & Architectural Recommendations", level=1)
    h2_rec.paragraph_format.space_before = Pt(14)
    h2_rec.paragraph_format.space_after = Pt(6)
    for r in h2_rec.runs:
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_rec = doc.add_paragraph(
        "To operationalize shared-collection multi-tenancy and data migrations at enterprise scale, "
        "engineering teams should implement the following architectural enhancements:\n\n"
        "1. Mandatory Compound Indexing:\n"
        "   In shared collections, every index must lead with the tenant discriminator: `{'tenant_id': 1, 'created_at': -1}` or "
        "`{'tenant_id': 1, 'status': 1}`. Leading with `tenant_id` prevents MongoDB from scanning index keys belonging to other tenants, "
        "maintaining high index selectivity and avoiding memory thrashing.\n\n"
        "2. TTL-Based Native Rate Limiting:\n"
        "   While `check_rate_limit()` accurately calculates call counts via `count_documents`, in high-throughput systems the "
        "`rate_limits` collection will grow unbounded. Creating a TTL (Time-To-Live) index:\n"
        "   `rate_col.create_index([('timestamp', 1)], expireAfterSeconds=60)`\n"
        "   allows MongoDB's background TTL thread to automatically purge expired request documents, preventing disk bloat.\n\n"
        "3. Application-Level Enforced Query Wrappers / ORM Middleware:\n"
        "   Relying on manual inclusion of `{'tenant_id': tenant_id}` in every query is prone to developer error. Production systems "
        "should utilize repository patterns or Mongoose/Motor middleware that automatically injects tenant context from the authenticated "
        "JWT/session into every outbound database operation.\n\n"
        "4. Dual-Writing During Zero-Downtime Live Migration:\n"
        "   In active production systems, migration occurs while writes are occurring. The migration pipeline must follow a 4-phase cutover:\n"
        "   • Phase 1: Dual-Write — Application writes new mutations to both shared collection and dedicated database.\n"
        "   • Phase 2: Historical Backfill — Idempotently copy historical records created prior to dual-writing.\n"
        "   • Phase 3: Cryptographic Verification — Validate record counts and SHA-256 checksums.\n"
        "   • Phase 4: Read Cutover & Source Deletion — Switch client read traffic to the dedicated database; archive and safely drop "
        "the tenant's records from the shared collection."
    )
    p_rec.paragraph_format.line_spacing = 1.15
    p_rec.paragraph_format.space_after = Pt(10)

    # 5. Conclusion & Verification Summary Table
    h2_concl = doc.add_heading("5. Verification Summary & Completion Sign-Off", level=1)
    h2_concl.paragraph_format.space_before = Pt(14)
    h2_concl.paragraph_format.space_after = Pt(6)
    for r in h2_concl.runs:
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    summary_table = doc.add_table(rows=6, cols=3)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    summary_table.autofit = False
    sum_widths = [Inches(2.5), Inches(1.5), Inches(2.5)]
    for row in summary_table.rows:
        for i, w in enumerate(sum_widths):
            row.cells[i].width = w

    sum_headers = ["Evaluation Criterion", "Test Status", "Observed System Behavior"]
    for i, h in enumerate(sum_headers):
        cell = summary_table.cell(0, i)
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    sum_rows = [
        ("Activity 1: Tenant-Scoped CRUD", "PASSED", "Tasks created, listed, and isolated cleanly per tenant."),
        ("Activity 1: Cross-Tenant Protection", "PASSED (BLOCKED)", "Globex cross-update blocked by {'_id': id, 'tenant_id': id} filter."),
        ("Activity 1: Rate Limiter", "PASSED", "Requests 1-10 allowed; requests 11-12 strictly rate limited."),
        ("Activity 2: Migration Dry-Run", "PASSED", "Reported 2 candidate tasks without mutating database."),
        ("Activity 2: Migration Idempotency & Rollback", "PASSED", "Repeat run maintained 2 documents; rollback successfully dropped target DB.")
    ]

    for r_idx, (crit, stat, obs) in enumerate(sum_rows, start=1):
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, text in enumerate([crit, stat, obs]):
            cell = summary_table.cell(r_idx, c_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(8.5)
            if c_idx == 1 and "PASSED" in text:
                run.bold = True
                run.font.color.rgb = RGBColor(0x28, 0xA7, 0x45)
            else:
                run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    set_table_borders(summary_table, color="D0D7DE", sz="4")

    # Output path
    output_path = r"c:\Users\aryap\OneDrive\Desktop\NoSQL_Lab_15\Lab_15_MultiTenant_API_and_Data_Migration_Report.docx"
    doc.save(output_path)
    print(f"Report saved successfully at: {output_path}")

if __name__ == "__main__":
    build_report()
