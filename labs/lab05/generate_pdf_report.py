"""PDF Report Generator for Lab 5: MongoDB Aggregation Pipeline & $lookup Joins
Author: K. Pranav Reddy (24BTRCL098)
Course: NoSQL Database Engineering
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, Preformatted
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "Lab 5: MongoDB Aggregation Pipeline & $lookup Joins")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "K. Pranav Reddy | 24BTRCL098")
            self.setStrokeColor(colors.HexColor("#D0D7DE"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#D0D7DE"))
        self.setLineWidth(0.5)
        self.line(54, 45, 8.5 * inch - 54, 45)
        self.drawString(54, 32, "NoSQL Database Engineering | Lab 5 Report")
        self.drawRightString(8.5 * inch - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(filename="Lab_05_24BTRCL098_K_Pranav_Reddy.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F294A"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1976D2"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F294A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1976D2"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#24292F"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#24292F"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1B2A4A")
    )

    table_text = ParagraphStyle(
        "TableText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#24292F")
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F294A")
    )

    story = []

    # Title & Header
    story.append(Paragraph("LAB REPORT: MONGO AGGREGATION & $LOOKUP JOINS", title_style))
    story.append(Paragraph("NoSQL Database Engineering | Lab 5 Practical Implementation & Analysis", subtitle_style))

    # Metadata Box
    meta_data = [
        [
            Paragraph("<b>Student Name:</b> K. Pranav Reddy", table_text),
            Paragraph("<b>Course:</b> NoSQL Database Engineering", table_text)
        ],
        [
            Paragraph("<b>Roll Number:</b> 24BTRCL098", table_text),
            Paragraph("<b>Database Engine:</b> MongoDB 7.0 Community", table_text)
        ],
        [
            Paragraph("<b>Artifacts:</b> lab_01_sales_analytics.py, lab_02_lookup_joins.py", table_text),
            Paragraph("<b>Status:</b> All Aggregations Tested & Verified", table_text)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[250, 254])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F6F8FA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#D0D7DE")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E1E4E8")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Section 1: Executive Overview
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "This laboratory exercises MongoDB's declarative Aggregation Framework, analyzing multi-stage pipelines "
        "and relational-style joins. We designed, executed, and benchmarked multi-stage data pipelines across two core activities: "
        "(1) <b>Sales Analytics Pipeline</b> using $match, $group, $sort, accumulators ($sum, $avg, $addToSet), "
        "and conditional expressions ($switch, $bucket); and (2) <b>Cross-Collection Joins</b> using $lookup, $unwind, "
        "and sub-pipeline left joins to detect unreferenced documents.",
        body_style
    ))

    # Section 2: Activity 1
    story.append(Paragraph("2. Activity 1: Build a Sales Analytics Pipeline", h1_style))
    story.append(Paragraph(
        "The aggregation pipeline model treats data transformations as declarative stages in a stream. Each stage "
        "processes documents emitted from the preceding stage, ensuring memory-efficient data flow.",
        body_style
    ))

    # Pre-lab task reflection
    story.append(Paragraph("2.1 Pre-Lab Formulation: Total Revenue per Category", h2_style))
    sketch_box = [
        [
            Paragraph(
                "<b>Pre-Lab Design Challenge:</b><br/>"
                "<i>'Sketch the stage sequence you'd use for total revenue per category, highest first on paper — "
                "it should be exactly three stages ($group, then $sort, and optionally a preceding $match).'</i><br/><br/>"
                "<b>Formulated Sequence:</b><br/>"
                "1. <b>Stage 1 ($match):</b> <code>{'status': 'completed'}</code> — Filters out unfulfilled/cancelled transactions early to minimize downstream aggregation workload.<br/>"
                "2. <b>Stage 2 ($group):</b> <code>{'_id': '$category', 'total_revenue': {'$sum': '$total'}, 'order_count': {'$sum': 1}}</code> — Buckets records by category and sums total revenue.<br/>"
                "3. <b>Stage 3 ($sort):</b> <code>{'total_revenue': -1}</code> — Orders resulting categories in descending order.<br/><br/>"
                "<b>Verification:</b> The sketched pipeline matches the verified implementation in <code>lab_01_sales_analytics.py</code>.",
                callout_style
            )
        ]
    ]
    t_sketch = Table(sketch_box, colWidths=[504])
    t_sketch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF3FB")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1976D2")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sketch)
    story.append(Spacer(1, 8))

    # Table 1: Category Revenue
    story.append(Paragraph("<b>Table 1: Total Revenue by Product Category (Completed Orders)</b>", h2_style))
    cat_data = [
        [Paragraph("Category", table_header), Paragraph("Total Revenue", table_header), Paragraph("Orders", table_header), Paragraph("Items Sold", table_header), Paragraph("Avg Value", table_header)],
        [Paragraph("Furniture", table_text), Paragraph("$5,900.00", table_text), Paragraph("2", table_text), Paragraph("7", table_text), Paragraph("$2,950.00", table_text)],
        [Paragraph("Electronics", table_text), Paragraph("$5,700.00", table_text), Paragraph("2", table_text), Paragraph("8", table_text), Paragraph("$2,850.00", table_text)],
        [Paragraph("Appliances", table_text), Paragraph("$5,600.00", table_text), Paragraph("1", table_text), Paragraph("8", table_text), Paragraph("$5,600.00", table_text)],
        [Paragraph("Apparel", table_text), Paragraph("$2,900.00", table_text), Paragraph("1", table_text), Paragraph("4", table_text), Paragraph("$2,900.00", table_text)],
        [Paragraph("Books", table_text), Paragraph("$2,700.00", table_text), Paragraph("2", table_text), Paragraph("3", table_text), Paragraph("$1,350.00", table_text)],
    ]
    t_cat = Table(cat_data, colWidths=[120, 100, 70, 84, 130])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F294A")),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 8))

    # Top Customers & Conditional Bucketing
    story.append(Paragraph("2.2 Top Customers and Conditional Order Bucketing", h2_style))
    story.append(Paragraph(
        "<b>Top 3 Customers:</b> Evaluated via <code>{'$match'} -> {'$group': {'_id': '$customer', 'total_spent': {'$sum': '$total'}}} -> {'$sort': {'total_spent': -1}} -> {'$limit': 3}</code>.<br/>"
        "• <b>#1 Arjun:</b> $6,900.00 (3 orders, 10 items)<br/>"
        "• <b>#2 Sneha:</b> $5,900.00 (2 orders, 7 items)<br/>"
        "• <b>#3 Rahul:</b> $5,600.00 (1 order, 8 items)<br/><br/>"
        "<b>Order Size Categorization using Conditional Logic:</b> Rather than using rigid static bucket stages, "
        "we leveraged <code>$switch</code> inside <code>$project</code> to categorize completed orders into business tiers: "
        "Small (&lt;$2,000), Medium ($2,000-$4,000), and Large (&gt;$4,000):",
        body_style
    ))

    size_data = [
        [Paragraph("Tier", table_header), Paragraph("Criteria", table_header), Paragraph("Order Count", table_header), Paragraph("Total Revenue", table_header), Paragraph("Orders Included", table_header)],
        [Paragraph("Large", table_text), Paragraph("total > $4,000", table_text), Paragraph("2", table_text), Paragraph("$9,700.00", table_text), Paragraph("ORD-105, ORD-107", table_text)],
        [Paragraph("Medium", table_text), Paragraph("$2,000 <= total <= $4,000", table_text), Paragraph("3", table_text), Paragraph("$8,600.00", table_text), Paragraph("ORD-101, ORD-103, ORD-108", table_text)],
        [Paragraph("Small", table_text), Paragraph("total < $2,000", table_text), Paragraph("3", table_text), Paragraph("$4,500.00", table_text), Paragraph("ORD-102, ORD-106, ORD-110", table_text)],
    ]
    t_size = Table(size_data, colWidths=[70, 130, 74, 90, 140])
    t_size.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F294A")),
        ('ALIGN', (2, 1), (3, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_size)
    story.append(Spacer(1, 10))

    # Section 3: Activity 2
    story.append(Paragraph("3. Activity 2: Cross-Collection Joins with $lookup", h1_style))
    story.append(Paragraph(
        "MongoDB's <code>$lookup</code> operator performs left outer joins between collections. Because joins in document stores "
        "can yield 0, 1, or multiple matches, the joined result is fundamentally an <b>array</b>. To normalize 1:1 relationships, "
        "the array is typically unwound using <code>$unwind</code>.",
        body_style
    ))

    # Pre-lab task reflection for Activity 2
    story.append(Paragraph("3.1 Pre-Lab Formulation: The 'Never Ordered' Left Join Pattern", h2_style))
    sketch_box_2 = [
        [
            Paragraph(
                "<b>Pre-Lab Theoretical Challenge:</b><br/>"
                "<i>'Before reading pipeline 2 in the source: write down, in your own words, what has to be true about the "
                "$lookup'd array for a product to count as never ordered.'</i><br/><br/>"
                "<b>Mathematical & Practical Rule:</b><br/>"
                "When joining from <code>products_join</code> into <code>orders_join</code>, the sub-pipeline matches all orders containing "
                "that product's ID. If a product was never purchased, the join encounters zero matching records, producing an "
                "<b>empty array</b> (<code>[]</code>). Thus, the exact necessary and sufficient condition is that the array's size is 0:<br/>"
                "<code>{'$match': {'ordered': {'$size': 0}}}</code><br/><br/>"
                "<b>Verification:</b> This perfectly matches the sub-pipeline filter implemented in <code>lab_02_lookup_joins.py</code>.",
                callout_style
            )
        ]
    ]
    t_sketch_2 = Table(sketch_box_2, colWidths=[504])
    t_sketch_2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#16A34A")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sketch_2)
    story.append(Spacer(1, 8))

    # Lookup Results Tables
    story.append(Paragraph("3.2 Empirical Join Results across Seeded Collections", h2_style))

    join_data = [
        [Paragraph("Pipeline Execution", table_header), Paragraph("Key Operators", table_header), Paragraph("Observed Behavior & Output", table_header)],
        [
            Paragraph("<b>1. Enriched Orders</b>", table_text),
            Paragraph("<code>$lookup, $unwind, $project</code>", table_text),
            Paragraph("Enriches orders with customer name, tier, and city. ORD-201 (Arjun, Gold, $350), ORD-202 (Sneha, Silver, $150), ORD-203 (Rahul, Platinum, $680), ORD-204 (Arjun, Gold, $0).", table_text)
        ],
        [
            Paragraph("<b>2. Never Ordered</b>", table_text),
            Paragraph("<code>$lookup + let, $match ($size: 0)</code>", table_text),
            Paragraph("Isolates dormant inventory: Successfully detected P006 (Sensor Pro F, $420) and P007 (Heavy Duty G, $110) with zero matching sales records.", table_text)
        ],
        [
            Paragraph("<b>3. Line Item Unwind</b>", table_text),
            Paragraph("<code>$unwind (preserveNull=True), $lookup</code>", table_text),
            Paragraph("Flattens product_ids array. Handles zero-item order ORD-204 without dropping the document, outputting '(no product)' and $0.00.", table_text)
        ],
        [
            Paragraph("<b>4. Customer 360 (Custom)</b>", table_text),
            Paragraph("<code>Reverse $lookup (Customers -> Orders)</code>", table_text),
            Paragraph("Aggregates customer lifetime spend ($LTV). Rahul: $680.00 (1 order), Arjun: $350.00 (2 orders), Sneha: $150.00 (1 order), Vikram: $0.00 (Never Ordered).", table_text)
        ],
    ]
    t_join = Table(join_data, colWidths=[120, 134, 250])
    t_join.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F294A")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_join)
    story.append(Spacer(1, 10))

    # Section 4: Architectural Best Practices
    story.append(Paragraph("4. Key Takeaways & Production Best Practices", h1_style))
    story.append(Paragraph(
        "• <b>Index Utilization & Early Filtering:</b> Place <code>$match</code> as the very first stage. When indexed, $match acts as an index scan filter, reducing the volume of BSON documents loaded into RAM by up to 99%.<br/>"
        "• <b>Memory Boundary Enforcement:</b> Individual aggregation stages have a hard memory ceiling of <b>100 MB</b>. For big-data analytical workloads exceeding 100 MB, the option <code>allowDiskUse=True</code> must be enabled.<br/>"
        "• <b>Defensive Unwinding:</b> When unwinding arrays that might be empty or null (e.g. newly initialized shopping carts), always specify <code>preserveNullAndEmptyArrays: True</code> to prevent data loss.<br/>"
        "• <b>Embedding vs Normalization:</b> In high-throughput NoSQL architectures, denormalizing line items inside orders eliminates the join overhead of $lookup entirely.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Verification Box
    story.append(Paragraph("5. Execution & Verification", h1_style))
    story.append(Paragraph(
        "To verify all pipelines and execute the complete test harness:<br/>"
        "<code>python run_all.py</code>",
        callout_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully built PDF report: {filename}")


if __name__ == "__main__":
    build_pdf()
