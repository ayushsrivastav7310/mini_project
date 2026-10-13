import csv
import io
from datetime import datetime
from typing import List
from flask import current_app
from app.models.waste_record import WasteRecord

def generate_csv_report(records: List[WasteRecord], start_date: str = "", end_date: str = "") -> str:
    """Generate a structured CSV audit report for biomedical waste compliance."""
    output = io.StringIO()
    writer = csv.writer(output)

    hospital_name = current_app.config.get("HOSPITAL_NAME", "Hospital BMW Facility")
    pcb_reg = current_app.config.get("PCB_REGISTRATION_NO", "N/A")

    # Header metadata
    writer.writerow([f"BIOMEDICAL WASTE GENERATION & DISPOSAL AUDIT REPORT - {hospital_name}"])
    writer.writerow([f"Pollution Control Board Reg. No: {pcb_reg}"])
    writer.writerow([f"Generated On: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"])
    if start_date or end_date:
        writer.writerow([f"Filter Range: {start_date or 'Start'} to {end_date or 'Present'}"])
    writer.writerow([])

    # Table Column Headers
    headers = [
        "Record ID",
        "Date & Time",
        "Department Code",
        "Department Name",
        "Item Description",
        "BMW Category",
        "Bin Color",
        "Quantity (kg)",
        "Staff Logged By",
        "Staff Verified?",
        "Verified By",
        "AI Suggested Category",
        "AI Confidence (%)",
        "Disposal Status",
        "Manifest / Vehicle",
        "Remarks"
    ]
    writer.writerow(headers)

    total_weight = 0.0
    for r in records:
        total_weight += r.quantity_kg
        writer.writerow([
            r.tracking_code,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
            r.department.code if r.department else "N/A",
            r.department.name if r.department else "N/A",
            r.item_description,
            r.category.name if r.category else "N/A",
            r.category.bin_color_name if r.category else "N/A",
            f"{r.quantity_kg:.2f}",
            r.logger.full_name if r.logger else "N/A",
            "YES" if r.staff_verified else "NO",
            r.verifier.full_name if r.verifier else "N/A",
            r.ai_suggested_category or "Manual Entry",
            f"{r.ai_confidence * 100:.1f}" if r.ai_confidence else "N/A",
            r.disposal_status,
            r.dispatch_manifest_no or "N/A",
            r.remarks or ""
        ])

    writer.writerow([])
    writer.writerow(["SUMMARY TOTALS"])
    writer.writerow(["Total Records", len(records)])
    writer.writerow(["Total Waste Generated (kg)", f"{total_weight:.2f}"])
    writer.writerow([])
    writer.writerow(["DISCLAIMER:", current_app.config.get("REGULATORY_DISCLAIMER", "")])

    return output.getvalue()


def generate_pdf_report(records: List[WasteRecord], start_date: str = "", end_date: str = "") -> bytes:
    """
    Generate an audit-grade PDF report using ReportLab.
    Includes institutional header, summary boxes, detailed records table, and signature block.
    """
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f5132"),
            alignment=1
        )
        sub_style = ParagraphStyle(
            "SubStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#495057"),
            alignment=1
        )
        body_style = ParagraphStyle(
            "BodySmall",
            parent=styles["Normal"],
            fontSize=8,
            leading=10
        )
        header_table_style = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=colors.white
        )

        elements = []

        # Hospital Header
        h_name = current_app.config.get("HOSPITAL_NAME", "Lifeline Hospital")
        pcb_code = current_app.config.get("PCB_REGISTRATION_NO", "PCB-BMW-0942")
        elements.append(Paragraph(f"<b>{h_name}</b>", title_style))
        elements.append(Paragraph(f"Biomedical Waste Management Ledger | PCB Registration: {pcb_code}", sub_style))
        elements.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%d-%b-%Y %H:%M UTC')} | Indian BMW Rules (2016) Compliance", sub_style))
        elements.append(Spacer(1, 12))

        # Summary Metrics
        total_weight = sum(r.quantity_kg for r in records)
        verified_count = sum(1 for r in records if r.staff_verified)
        dispatched_weight = sum(r.quantity_kg for r in records if r.disposal_status == WasteRecord.STATUS_DISPATCHED)

        summary_data = [
            ["Total Waste Records", "Total Generated", "Verified by Staff", "Dispatched for Treatment"],
            [f"{len(records)} entries", f"{total_weight:.2f} kg", f"{verified_count} ({round(verified_count/len(records)*100, 1) if records else 0}%)", f"{dispatched_weight:.2f} kg"]
        ]
        summary_table = Table(summary_data, colWidths=[180, 180, 180, 180])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#212529")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8f9fa")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # Records Table
        table_headers = [
            Paragraph("<b>Code</b>", header_table_style),
            Paragraph("<b>Date/Time</b>", header_table_style),
            Paragraph("<b>Dept</b>", header_table_style),
            Paragraph("<b>Item Description</b>", header_table_style),
            Paragraph("<b>Category</b>", header_table_style),
            Paragraph("<b>Weight</b>", header_table_style),
            Paragraph("<b>Status</b>", header_table_style),
            Paragraph("<b>Staff</b>", header_table_style),
            Paragraph("<b>Verified</b>", header_table_style),
        ]
        
        table_rows = [table_headers]
        for r in records[:150]:  # Cap at 150 records per PDF report for performance
            verified_label = "Yes" if r.staff_verified else "No"
            table_rows.append([
                Paragraph(r.tracking_code, body_style),
                Paragraph(r.created_at.strftime("%d-%b %H:%M"), body_style),
                Paragraph(r.department.code if r.department else "-", body_style),
                Paragraph(r.item_description[:25], body_style),
                Paragraph(r.category.bin_color_name if r.category else "-", body_style),
                Paragraph(f"{r.quantity_kg:.2f} kg", body_style),
                Paragraph(r.disposal_status, body_style),
                Paragraph(r.logger.full_name[:15] if r.logger else "-", body_style),
                Paragraph(verified_label, body_style),
            ])

        col_widths = [85, 65, 45, 170, 75, 55, 65, 90, 45]
        records_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        records_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#198754")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        elements.append(records_table)
        elements.append(Spacer(1, 20))

        # Signatures and Legal Disclaimer
        disclaimer_text = current_app.config.get("REGULATORY_DISCLAIMER", "")
        elements.append(Paragraph(f"<i>{disclaimer_text}</i>", sub_style))
        elements.append(Spacer(1, 15))

        sig_data = [
            ["_________________________", "_________________________"],
            ["Biomedical Waste Supervisor", "Infection Control Officer / Medical Superintendent"],
            ["Date: ___________________", "Official Stamp & Signature"]
        ]
        sig_table = Table(sig_data, colWidths=[360, 360])
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(KeepTogether([sig_table]))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except ImportError:
        # Fallback if ReportLab is not installed: create printable HTML / text-based document
        text_output = generate_csv_report(records, start_date, end_date)
        return text_output.encode("utf-8")
