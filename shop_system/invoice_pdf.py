"""
Invoice PDF Generator — produces a clean, printable invoice.
Uses reportlab. Output goes to a temp file, opened by the OS PDF viewer.
"""

import os
import tempfile
from datetime import datetime
import business


def generate_invoice_pdf(session, sale) -> str:
    """Generate a PDF invoice for the given Sale object. Returns the PDF file path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    except ImportError:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    # ---- settings ----
    shop_name    = business.get_setting(session, "shop_name", "My Shop")
    shop_address = business.get_setting(session, "shop_address", "")
    shop_phone   = business.get_setting(session, "shop_phone", "")
    currency     = business.get_setting(session, "currency", "Rs.")

    # ---- output path ----
    invoice_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
    os.makedirs(invoice_dir, exist_ok=True)
    filename = f"Invoice_{sale.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(invoice_dir, filename)

    # ---- styles ----
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    styles = getSampleStyleSheet()
    W = A4[0] - 40*mm   # usable width

    def style(name, **kw):
        s = ParagraphStyle(name, parent=styles["Normal"], **kw)
        return s

    DARK   = colors.HexColor("#1A1D23")
    ACCENT = colors.HexColor("#2D9CDB")
    GRAY   = colors.HexColor("#6B7280")
    LIGHT  = colors.HexColor("#F3F4F6")
    WHITE  = colors.white

    story = []

    # ---- Header ----
    header_data = [[
        Paragraph(f"<b><font size=20>{shop_name}</font></b>", style("sh", textColor=DARK)),
        Paragraph(
            f"<b><font size=16 color='#2D9CDB'>INVOICE</font></b><br/>"
            f"<font size=9 color='#6B7280'>{sale.invoice_number}</font>",
            style("ih", alignment=TA_RIGHT)
        )
    ]]
    tbl = Table(header_data, colWidths=[W*0.55, W*0.45])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(tbl)

    # Shop info + Invoice meta
    date_str = sale.date.strftime("%d %B %Y  %I:%M %p")
    status_color = {"paid": "#27AE60", "partial": "#F2994A", "unpaid": "#EB5757"}.get(
        sale.status, "#6B7280")

    meta_data = [[
        Paragraph(
            (f"{shop_address}<br/>" if shop_address else "") +
            (f"📞 {shop_phone}" if shop_phone else ""),
            style("sm", textColor=GRAY, fontSize=9)
        ),
        Paragraph(
            f"<b>Date:</b> {date_str}<br/>"
            f"<b>Status:</b> <font color='{status_color}'><b>{sale.status.upper()}</b></font>",
            style("mr", alignment=TA_RIGHT, fontSize=10)
        )
    ]]
    tbl2 = Table(meta_data, colWidths=[W*0.55, W*0.45])
    tbl2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(tbl2)
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))

    # Customer block
    cust_name = sale.customer_name or "Walk-in Customer"
    cust_para = Paragraph(
        f"<b>Bill To:</b><br/>"
        f"<font size=12><b>{cust_name}</b></font>",
        style("ct", fontSize=10)
    )
    if sale.customer:
        c = sale.customer
        extras = []
        if c.phone:    extras.append(f"📞 {c.phone}")
        if c.address:  extras.append(c.address)
        if extras:
            cust_para = Paragraph(
                f"<b>Bill To:</b><br/>"
                f"<font size=12><b>{cust_name}</b></font><br/>"
                f"<font size=9 color='#6B7280'>{' | '.join(extras)}</font>",
                style("ct", fontSize=10)
            )
    story.append(cust_para)
    story.append(Spacer(1, 12))

    # ---- Items table ----
    # 4 columns: Product | Qty | Unit Price | Amount
    col_widths = [W*0.45, W*0.12, W*0.22, W*0.21]
    items_header = [
        Paragraph("<b>Product</b>", style("th", fontSize=9, textColor=WHITE)),
        Paragraph("<b>Qty</b>", style("th", fontSize=9, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("<b>Unit Price</b>", style("th", fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
        Paragraph("<b>Amount</b>", style("th", fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
    ]

    rows = [items_header]
    for si in sale.sale_items:
        p = si.product
        size_str = f" [{p.display_size}]" if p and p.display_size else ""
        rows.append([
            Paragraph(f"{si.product_name}{size_str}", style("td", fontSize=9)),
            Paragraph(str(si.quantity), style("td", fontSize=9, alignment=TA_CENTER)),
            Paragraph(f"{currency} {si.unit_price:,.0f}", style("td", fontSize=9, alignment=TA_RIGHT)),
            Paragraph(f"{currency} {si.line_total:,.0f}", style("td", fontSize=9, alignment=TA_RIGHT)),
        ])

    items_tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0,0), (-1,0), DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
        ("FONTSIZE",      (0,1), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 12))

    # ---- Totals ----
    def money(amount):
        return f"{currency} {amount:,.0f}"

    totals_data = []
    totals_data.append(["Subtotal", money(sale.subtotal)])
    if sale.discount_amount > 0:
        disc_label = (
            f"Discount ({sale.discount_value:.0f}%)"
            if sale.discount_type == "percent"
            else "Discount (flat)"
        )
        totals_data.append([disc_label, f"– {money(sale.discount_amount)}"])
    totals_data.append(["TOTAL", money(sale.total)])
    totals_data.append(["Amount Paid", money(sale.amount_paid)])
    totals_data.append(["Amount Due", money(sale.amount_due)])

    tot_table_data = []
    for i, (label, value) in enumerate(totals_data):
        is_total = label == "TOTAL"
        tot_table_data.append([
            Paragraph(f"<b>{label}</b>" if is_total else label,
                      style(f"tl{i}", fontSize=9 if not is_total else 11,
                            alignment=TA_RIGHT)),
            Paragraph(f"<b>{value}</b>" if is_total else value,
                      style(f"tv{i}", fontSize=9 if not is_total else 11,
                            alignment=TA_RIGHT,
                            textColor=ACCENT if is_total else
                                       colors.HexColor("#EB5757") if label == "Amount Due" and sale.amount_due > 0
                                       else colors.HexColor("#1A1D23")))
        ])

    tot_tbl = Table(tot_table_data, colWidths=[W*0.7, W*0.3])
    tot_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEABOVE",     (0, len(totals_data)-3), (-1, len(totals_data)-3), 0.5, GRAY),
    ]))
    story.append(tot_tbl)
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceBefore=12, spaceAfter=12))

    # Notes
    if sale.notes:
        story.append(Paragraph(f"<b>Notes:</b> {sale.notes}",
                               style("notes", fontSize=9, textColor=GRAY)))
        story.append(Spacer(1, 8))

    # Footer
    story.append(Paragraph(
        f"Thank you for your business!",
        style("footer", alignment=TA_CENTER, textColor=ACCENT, fontSize=10, spaceAfter=4)
    ))
    story.append(Paragraph(
        f"Generated by Shop System  ·  {datetime.now().strftime('%d %b %Y %H:%M')}",
        style("gen", alignment=TA_CENTER, textColor=GRAY, fontSize=8)
    ))

    doc.build(story)
    return pdf_path
