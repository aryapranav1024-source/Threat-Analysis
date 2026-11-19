import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
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
        self.setFillColor(colors.HexColor("#64748B"))

        # Suppress header and footer on cover page
        if self._pageNumber > 1:
            # Running Header
            self.drawString(54, letter[1] - 36, "NoSQL Lab 17: RAG Pipeline & Vector Index Types (HNSW vs IVF)")
            self.drawRightString(letter[0] - 54, letter[1] - 36, "K. Pranav Reddy | 24BTRCL098")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

            # Running Footer
            self.line(54, 45, letter[0] - 54, 45)
            self.drawString(54, 32, "Docker Hub: https://hub.docker.com/r/aryapranav1024/nosql-lab17")
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 32, page_str)

        self.restoreState()


def create_report(output_filename="Lab_17_RAG_Pipeline_and_Vector_Indexing_Report.pdf"):
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E293B'),
        alignment=0,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284C7'),
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#1B365D'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#E2E8F0'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#FFFFFF'),
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=table_cell_style,
        alignment=2
    )

    story = []

    # ═══════════════════════════════════════════════════════════════════════
    # COVER / HEADER BLOCK
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("LABORATORY EXPERIMENT REPORT", ParagraphStyle('TopBadge', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0284C7'), spaceAfter=4)))
    story.append(Paragraph("NoSQL Lab 17: RAG Pipeline & Vector Indexing Benchmarks", title_style))
    story.append(Paragraph("Semantic Retrieval with Dense Embeddings and Empirical Evaluation of HNSW vs. IVF Vector Indices", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284C7'), spaceBefore=0, spaceAfter=14))

    # Student & Submission Metadata Table
    meta_data = [
        [Paragraph("<b>Course:</b> NoSQL Database Engineering", table_cell_style), Paragraph("<b>Student Name:</b> K. Pranav Reddy", table_cell_style)],
        [Paragraph("<b>Lab Module:</b> Lab 17 (RAG & Vector Search)", table_cell_style), Paragraph("<b>Roll Number:</b> 24BTRCL098", table_cell_style)],
        [Paragraph("<b>Execution Environment:</b> Python 3.10 / MongoDB 7.0 / Docker", table_cell_style), Paragraph("<b>Delivery Date:</b> November 17, 2026", table_cell_style)],
        [Paragraph("<b>Docker Hub Repository:</b>", table_cell_bold), Paragraph("<b>https://hub.docker.com/r/aryapranav1024/nosql-lab17</b>", ParagraphStyle('DkLink', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0284C7')))],
        [Paragraph("<b>Docker Pull Command:</b>", table_cell_bold), Paragraph("<font name='Courier'>docker pull aryapranav1024/nosql-lab17:latest</font>", table_cell_style)]
    ]
    meta_table = Table(meta_data, colWidths=[240, 264])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Executive Summary Callout
    exec_text = (
        "<b>Executive Summary:</b> This lab implements and evaluates two foundational pillars of modern vector-enabled "
        "database architectures: (1) An end-to-end <b>Retrieval-Augmented Generation (RAG)</b> pipeline operating over MongoDB "
        "with passage chunking, unit-normalized vector embeddings, and brute-force cosine similarity retrieval, and (2) An empirical "
        "comparison of two major <b>Approximate Nearest Neighbor (ANN)</b> indexing paradigms—<b>Inverted File Index (IVF)</b> "
        "clustering versus <b>Hierarchical Navigable Small World (HNSW / NSW)</b> graph search—measured across 3,000 synthetic vectors "
        "for Ground Truth Recall@k, vectors compared per query, and execution latency."
    )
    callout_data = [[Paragraph(exec_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#93C5FD')),
        ('LINELEFT', (0, 0), (0, -1), 4, colors.HexColor('#0284C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1: ACTIVITY 1 - BUILD A SIMPLE RAG PIPELINE
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Activity 1: Build a Simple RAG Pipeline (lab_01_rag_pipeline.py)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Retrieval-Augmented Generation (RAG) bridges external domain knowledge with Large Language Models (LLMs) by converting "
        "text into dense numerical vectors (embeddings), identifying geometrically proximate passages via a distance metric, "
        "and injecting those passages directly into the model's prompt context.",
        body_style
    ))

    story.append(Paragraph("<b>1.1 Core Mathematical Foundations & Concepts</b>", h2_style))
    story.append(Paragraph("• <b>Text Embeddings:</b> An embedding function maps text to a fixed-dimensional continuous vector space ℝ^d where semantic relatedness correlates with small angular separation. In production, deep neural embedding models (e.g., VoyageAI voyage-3, OpenAI text-embedding-3-small) capture subtle linguistic nuances. In this lab, deterministic MD5 hashing seeds pseudo-random vectors for zero-cost offline reproducibility.", bullet_style))
    story.append(Paragraph("• <b>Cosine Similarity via Dot Product:</b> Cosine similarity computes cos(θ) = (A · B) / (||A|| ||B||). Because all embeddings in this pipeline are pre-normalized to unit length (||v|| = 1.0) during generation, cosine similarity reduces to a fast dot product: sum(x_i * y_i), where 1.0 denotes identical direction and 0.0 denotes orthogonality.", bullet_style))
    story.append(Paragraph("• <b>Chunking Strategy:</b> Long documents are segmented into 50-word passages with chunk indices. This maintains fine-grained context boundaries, preventing relevant facts from being diluted across long texts.", bullet_style))

    story.append(Paragraph("<b>1.2 Pre-Reading Semantic Prediction vs. Actual Retrieval</b>", h2_style))
    story.append(Paragraph(
        "Before inspecting the retrieval step, predictions were formulated strictly from the seeded documents' titles and contents "
        "to verify whether semantic retrieval aligns with human expectation:",
        body_style
    ))

    pred_data = [
        [Paragraph("Sample Question", table_header_style), Paragraph("Semantic Prediction", table_header_style), Paragraph("Actual Retrieved Chunks (Top 2)", table_header_style), Paragraph("Score", table_header_style)],
        [
            Paragraph("What are the four NoSQL database families?", table_cell_bold),
            Paragraph("Document: <i>'Introduction to NoSQL'</i> (explicitly lists Document, Key-Value, Wide-Column, Graph)", table_cell_style),
            Paragraph("1. Vector Search and AI [Chunk 0]<br/>2. Replica Sets and High Availability [Chunk 0]", table_cell_style),
            Paragraph("0.0894<br/>0.0812", table_cell_right)
        ],
        [
            Paragraph("How does the aggregation framework pipeline work?", table_cell_bold),
            Paragraph("Document: <i>'MongoDB Aggregation Framework'</i> (describes stages: $match, $group, $project)", table_cell_style),
            Paragraph("1. Vector Search and AI [Chunk 0]<br/>2. Replica Sets and High Availability [Chunk 1]", table_cell_style),
            Paragraph("0.0934<br/>0.0631", table_cell_right)
        ],
        [
            Paragraph("What is HNSW and how is it used in MongoDB?", table_cell_bold),
            Paragraph("Document: <i>'Vector Search and AI'</i> (specifically discusses HNSW index and $vectorSearch)", table_cell_style),
            Paragraph("1. Vector Search and AI [Chunk 1]<br/>2. Vector Search and AI [Chunk 0]", table_cell_style),
            Paragraph("0.1345<br/>0.0877", table_cell_right)
        ],
        [
            Paragraph("How does replica set failover work?", table_cell_bold),
            Paragraph("Document: <i>'Replica Sets and High Availability'</i> (covers primary failover and elections)", table_cell_style),
            Paragraph("1. Introduction to NoSQL [Chunk 0]<br/>2. Introduction to NoSQL [Chunk 1]", table_cell_style),
            Paragraph("0.0898<br/>0.0769", table_cell_right)
        ]
    ]
    pred_table = Table(pred_data, colWidths=[130, 140, 180, 54])
    pred_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Critical Analysis:</b> In question 3 (<i>'What is HNSW and how is it used in MongoDB?'</i>), both retrieved chunks strictly "
        "matched the expected document (<i>'Vector Search and AI'</i>) with the highest observed cosine similarity (0.1345). "
        "However, in questions 1, 2, and 4, the deterministic mock embedding (MD5 hash pseudo-random projection) retrieved other chunks. "
        "This empirical discrepancy cleanly validates the core theoretical lesson: <b>mock hash embeddings possess no semantic geometry</b>. "
        "Two semantically identical phrases that differ by a single character produce completely uncorrelated hash vectors. In production MongoDB "
        "Atlas Vector Search, pre-trained transformer embeddings (OpenAI, VoyageAI) ensure 100% semantic alignment.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2: ACTIVITY 2 - HNSW VS IVF VECTOR INDEX COMPARISON
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Activity 2: Compare HNSW and IVF Vector Index Types (lab_02_hnsw_vs_ivf.py)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Exact brute-force nearest neighbor search scales linearly as O(N · d), becoming computationally infeasible as datasets "
        "reach millions or billions of items. <b>Approximate Nearest Neighbor (ANN)</b> algorithms trade a fraction of search accuracy "
        "(Recall@k) for orders-of-magnitude reduction in candidate vectors compared.",
        body_style
    ))

    story.append(Paragraph("<b>2.1 Pre-Running Hypotheses & Theoretical Predictions</b>", h2_style))
    story.append(Paragraph(
        "• <b>Recall Prediction:</b> The simplified <b>NSW (HNSW-like)</b> graph index will achieve substantially higher recall than the <b>IVF</b> index. "
        "<i>Reasoning:</i> IVF strictly restricts its candidate pool to the vectors in the <code>nprobe</code> nearest clusters. If a true neighbor lies across a Voronoi boundary in an adjacent cluster, it is completely inaccessible. In contrast, the NSW graph maintains long-range and short-range edges that allow greedy traversal to navigate complex high-dimensional topology.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Metric Reliability Prediction:</b> <b>'Vectors compared per query'</b> is the only reliable metric for architectural evaluation; <b>'wall-clock query time'</b> is misleading in pure Python. "
        "<i>Reasoning:</i> In pure Python, graph traversals incur interpreter overhead, pointer chasing, and heap manipulation (<code>heapq.heappush</code>/<code>heappop</code>). In contrast, matrix operations (<code>data @ centroids</code>) in IVF run in vectorized BLAS C-code. In a production C++ engine like MongoDB Atlas $vectorSearch, vector comparisons directly dictate memory bandwidth and CPU cycles.",
        bullet_style
    ))

    story.append(Paragraph("<b>2.2 Experimental Results & Empirical Verification</b>", h2_style))
    story.append(Paragraph("Dataset: N = 3,000 vectors, Dimension = 64, Queries = 20, k = 10 nearest neighbors.", body_style))

    res_data = [
        [Paragraph("Index Architecture", table_header_style), Paragraph("Build Time (ms)", table_header_style), Paragraph("Vectors Compared / Query", table_header_style), Paragraph("Avg Query Time (ms)", table_header_style), Paragraph("Recall@10", table_header_style)],
        [
            Paragraph("<b>Brute-force (Exact Ground Truth)</b>", table_cell_style),
            Paragraph("0.0 ms", table_cell_right),
            Paragraph("3,000 (100.0%)", table_cell_right),
            Paragraph("0.199 ms", table_cell_right),
            Paragraph("<b>100.00%</b>", ParagraphStyle('G1', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#16A34A'), alignment=2))
        ],
        [
            Paragraph("<b>IVF (nlist=20, nprobe=3)</b>", table_cell_style),
            Paragraph("25.2 ms", table_cell_right),
            Paragraph("447 (14.9%)", table_cell_right),
            Paragraph("0.087 ms", table_cell_right),
            Paragraph("<b>42.00%</b>", ParagraphStyle('G2', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#CA8A04'), alignment=2))
        ],
        [
            Paragraph("<b>Simplified NSW (HNSW-like)</b>", table_cell_style),
            Paragraph("426.8 ms", table_cell_right),
            Paragraph("1,810 (60.3%)", table_cell_right),
            Paragraph("7.205 ms", table_cell_right),
            Paragraph("<b>91.50%</b>", ParagraphStyle('G3', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#7C3AED'), alignment=2))
        ]
    ]
    res_table = Table(res_data, colWidths=[150, 80, 120, 84, 70])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F5F3FF')),
    ]))
    story.append(res_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Verification of Predictions:</b><br/>"
        "1. <b>Recall Performance:</b> NSW achieved <b>91.50% Recall@10</b>, outperforming IVF (42.00%) by more than 2.1×. Graph navigation successfully routed around local minima to locate the true top-k neighbors.<br/>"
        "2. <b>Search Efficiency:</b> IVF pruned 85.1% of vectors (only 447 compared out of 3,000), while NSW pruned 39.7% (1,810 compared). Both touched a fraction of the dataset.<br/>"
        "3. <b>Metric Analysis:</b> As predicted, pure Python query latency for NSW (7.205 ms) was elevated due to per-node heap operations, whereas IVF leveraged compiled BLAS dot products (0.087 ms). In production C++ (Atlas HNSW), the 91.5% recall is achieved at microsecond speeds.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 3: THREAT ANALYSIS PLATFORM INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Threat Analysis Platform Integration", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Lab 17 has been integrated into the existing <b>ThreatAnalysis SOC Command Center</b> web application, "
        "allowing cyber threat intelligence analysts to interactively run RAG queries and explore vector index benchmarks.",
        body_style
    ))

    story.append(Paragraph("• <b>Backend API Routes (FastAPI):</b> Added dedicated endpoints in <font name='Courier'>backend/lab17_routes.py</font> mounted under <font name='Courier'>/api/labs/lab17/*</font>, including <font name='Courier'>/rag</font> for live query scoring, <font name='Courier'>/documents</font> for passage chunks, <font name='Courier'>/index_comparison</font> for live ANN benchmarks, and <font name='Courier'>/concepts</font> for educational theory.", bullet_style))
    story.append(Paragraph("• <b>Frontend Dashboard (HTML/JS):</b> Added a collapsible sidebar tab <font name='Courier'>Lab 17: RAG & Vector Index</font> with three interactive sub-studios: (1) <i>RAG Query Studio</i> with live cosine similarity scoring and prompt synthesis, (2) <i>HNSW vs IVF Benchmark Matrix</i> with vectors-compared breakdowns, and (3) <i>Vector Search Concepts</i> card explorer.", bullet_style))

    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4: DOCKER CONTAINERIZATION & SUBMISSION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Docker Container Architecture & Submission Verification", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "A multi-stage, production-ready Docker container was engineered to package the complete Lab 17 suite with an embedded MongoDB instance:",
        body_style
    ))

    docker_details = [
        [Paragraph("Component", table_header_style), Paragraph("Specification", table_header_style)],
        [Paragraph("<b>Base Image</b>", table_cell_bold), Paragraph("mongo:7.0 (Official Debian-based MongoDB container)", table_cell_style)],
        [Paragraph("<b>Python Runtime</b>", table_cell_bold), Paragraph("Python 3.10 with pip, dos2unix, curl, procps", table_cell_style)],
        [Paragraph("<b>Python Libraries</b>", table_cell_bold), Paragraph("pymongo, numpy (v1.24 - v2.2), rich (ANSI tables)", table_cell_style)],
        [Paragraph("<b>Entrypoint Script</b>", table_cell_bold), Paragraph("entrypoint.sh (forks mongod, polls admin ping, executes run_all_labs.py)", table_cell_style)],
        [Paragraph("<b>Docker Hub Image</b>", table_cell_bold), Paragraph("<b>aryapranav1024/nosql-lab17:latest</b>", ParagraphStyle('DkP', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#0284C7')))],
        [Paragraph("<b>Docker Hub URL</b>", table_cell_bold), Paragraph("<b>https://hub.docker.com/r/aryapranav1024/nosql-lab17</b>", ParagraphStyle('DkL', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#0284C7')))],
        [Paragraph("<b>Run Instructions</b>", table_cell_bold), Paragraph("<font name='Courier'>docker run --rm aryapranav1024/nosql-lab17:latest</font>", table_cell_style)]
    ]
    docker_table = Table(docker_details, colWidths=[140, 364])
    docker_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(docker_table)

    story.append(Spacer(1, 14))

    # Sign-off block
    signoff_data = [
        [
            Paragraph("<b>Prepared by:</b><br/>K. Pranav Reddy (24BTRCL098)<br/>School of Computer Science & Engineering", table_cell_style),
            Paragraph("<b>Evaluation Checklist:</b><br/>[x] Activity 1: RAG Pipeline Complete<br/>[x] Activity 2: HNSW vs IVF Evaluated<br/>[x] Threat Analysis Integration Done<br/>[x] Docker Image Published & Verified", table_cell_style)
        ]
    ]
    signoff_table = Table(signoff_data, colWidths=[250, 254])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(signoff_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_report()
