"""
Real-Time Automated Excel Export Utility for 3D Printing Defect Detection.
Extracts all live inspection records, defect detections, bounding box coordinates,
and statistical telemetry from SQLite and formats a production-grade multi-tab
Excel workbook.

Usage:
    python export_inspection_results_excel.py
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "database" / "defect_detection.db"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "3D_Printing_Defect_Inspection_Results_Output.xlsx"


def generate_inspection_output_excel(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """
    Connect to database, extract all inspection runs and bounding box detections,
    and generate a fully-styled analytical Excel output report.
    """
    if not DB_PATH.exists():
        print(f"Error: Database file not found at {DB_PATH}")
        return output_path

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch Master Inspections
    cursor.execute("""
        SELECT 
            i.id,
            i.inspection_type,
            i.original_filename,
            i.result_filename,
            i.defect_type,
            i.confidence,
            i.status,
            i.timestamp,
            i.processing_time,
            i.source,
            i.notes,
            COUNT(d.id) AS detection_count
        FROM inspections i
        LEFT JOIN detections d ON i.id = d.inspection_id
        GROUP BY i.id
        ORDER BY i.id ASC
    """)
    inspections_data = cursor.fetchall()

    # 2. Fetch Detailed Detections
    cursor.execute("""
        SELECT 
            d.id AS detection_id,
            d.inspection_id,
            i.inspection_type,
            d.class_name,
            d.confidence,
            d.x1,
            d.y1,
            d.x2,
            d.y2,
            ROUND(d.x2 - d.x1, 2) AS box_width,
            ROUND(d.y2 - d.y1, 2) AS box_height,
            ROUND((d.x2 - d.x1) * (d.y2 - d.y1), 2) AS box_area,
            d.timestamp
        FROM detections d
        JOIN inspections i ON d.inspection_id = i.id
        ORDER BY d.id ASC
    """)
    detections_data = cursor.fetchall()
    conn.close()

    # Create Workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Styling definitions
    font_family = "Segoe UI"
    font_title = Font(name=font_family, size=14, bold=True, color="FFFFFF")
    font_section = Font(name=font_family, size=11, bold=True, color="1A365D")
    font_kpi_label = Font(name=font_family, size=9, bold=True, color="4A5568")
    font_kpi_val = Font(name=font_family, size=16, bold=True, color="1A365D")
    font_header = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    font_body = Font(name=font_family, size=9.5, color="2D3748")
    font_bold = Font(name=font_family, size=9.5, bold=True, color="2D3748")
    font_good = Font(name=font_family, size=9.5, bold=True, color="22543D")
    font_defect = Font(name=font_family, size=9.5, bold=True, color="742A2A")

    fill_navy = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    fill_blue = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
    fill_teal = PatternFill(start_color="2C7A7B", end_color="2C7A7B", fill_type="solid")
    fill_kpi_bg = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
    fill_zebra_1 = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_zebra_2 = PatternFill(start_color="F7FAFC", end_color="F7FAFC", fill_type="solid")
    fill_good = PatternFill(start_color="C6F6D5", end_color="C6F6D5", fill_type="solid")
    fill_defect = PatternFill(start_color="FED7D7", end_color="FED7D7", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    thick_border = Border(
        left=Side(style='medium', color='1A365D'),
        right=Side(style='medium', color='1A365D'),
        top=Side(style='medium', color='1A365D'),
        bottom=Side(style='medium', color='1A365D')
    )

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    # -------------------------------------------------------------
    # SHEET 1: Executive_Summary_KPIs
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="Executive_Summary_KPIs")
    ws1.views.sheetView[0].showGridLines = True

    ws1.merge_cells("A1:G2")
    ws1["A1"] = "3D PRINTING DEFECT DETECTION - SYSTEM INSPECTION TELEMETRY SUMMARY"
    ws1["A1"].font = font_title
    ws1["A1"].fill = fill_navy
    ws1["A1"].alignment = align_center

    total_inspections = len(inspections_data)
    good_count = sum(1 for row in inspections_data if row["status"] == "GOOD")
    defect_count = sum(1 for row in inspections_data if row["status"] == "DEFECT")
    total_boxes = len(detections_data)
    
    avg_conf = (sum(row["confidence"] for row in inspections_data) / total_inspections) if total_inspections > 0 else 0.0
    avg_time = (sum(row["processing_time"] for row in inspections_data if row["processing_time"]) / total_inspections) if total_inspections > 0 else 0.0
    defect_rate = (defect_count / total_inspections) if total_inspections > 0 else 0.0

    # KPI Card Blocks
    kpis = [
        ("Total Inspections Run", f"{total_inspections:,}", "A4", "B5", fill_kpi_bg),
        ("Defects Identified", f"{defect_count:,}", "C4", "C5", fill_defect),
        ("Normal / Good Prints", f"{good_count:,}", "D4", "D5", fill_good),
        ("System Defect Rate", f"{defect_rate:.1%}", "E4", "E5", fill_kpi_bg),
        ("Avg Confidence Score", f"{avg_conf:.1%}", "F4", "F5", fill_kpi_bg),
        ("Avg Processing Time", f"{avg_time:.1f} ms", "G4", "G5", fill_kpi_bg),
    ]

    for label, val, top_left, bot_right, fill_style in kpis:
        c_top = ws1[top_left.split(":")[0]]
        c_top.value = label
        c_top.font = font_kpi_label
        c_top.alignment = align_center
        c_top.fill = fill_style
        c_top.border = thin_border
        
        # If merged or single cell:
        col = top_left[0]
        row_num = int(top_left[1:]) + 1
        c_val = ws1[f"{col}{row_num}"]
        c_val.value = val
        c_val.font = font_kpi_val
        c_val.alignment = align_center
        c_val.fill = fill_style
        c_val.border = thin_border

    # Section 2: Defect Classification Breakdown
    ws1["A8"] = "Defect Classification Breakdown & Frequency Analysis"
    ws1["A8"].font = font_section

    d_breakdown_headers = ["Defect Category", "Total Occurrences", "Share of Total Defects", "Average Confidence", "Operational Severity"]
    ws1.row_dimensions[9].height = 24
    for col_idx, h in enumerate(d_breakdown_headers, 1):
        cell = ws1.cell(row=9, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_blue
        cell.alignment = align_center
        cell.border = thin_border

    # Count occurrences by defect_type
    defect_counts = {}
    defect_conf_sum = {}
    for row in inspections_data:
        dtype = row["defect_type"] or "Normal / Good Print"
        defect_counts[dtype] = defect_counts.get(dtype, 0) + 1
        defect_conf_sum[dtype] = defect_conf_sum.get(dtype, 0.0) + (row["confidence"] or 0.0)

    severity_map = {
        "Spaghetti Failure": "CRITICAL (Immediate Halt)",
        "Layer Shift": "HIGH (Structural Ruin)",
        "Warping": "HIGH (Detachment Risk)",
        "Under-Extrusion": "MEDIUM (Porous / Weak)",
        "Over-Extrusion": "LOW (Dimensional Flaw)",
        "Stringing": "LOW (Cosmetic Cleanup)",
        "Good Print": "NOMINAL (Passing Quality)",
        "Normal / Good Print": "NOMINAL (Passing Quality)",
    }

    curr_row = 10
    for dtype, count in sorted(defect_counts.items(), key=lambda x: x[1], reverse=True):
        ws1.row_dimensions[curr_row].height = 20
        bg = fill_zebra_2 if curr_row % 2 == 1 else fill_zebra_1
        avg_c = (defect_conf_sum[dtype] / count) if count > 0 else 0.0
        share = (count / total_inspections) if total_inspections > 0 else 0.0
        sev = severity_map.get(dtype, "MONITORED")

        ws1.cell(row=curr_row, column=1, value=dtype).font = font_bold
        ws1.cell(row=curr_row, column=2, value=count).number_format = "#,##0"
        ws1.cell(row=curr_row, column=3, value=share).number_format = "0.00%"
        ws1.cell(row=curr_row, column=4, value=avg_c).number_format = "0.00%"
        ws1.cell(row=curr_row, column=5, value=sev).font = font_defect if "CRITICAL" in sev or "HIGH" in sev else font_body

        for c_idx in range(1, 6):
            cell = ws1.cell(row=curr_row, column=c_idx)
            cell.fill = bg
            cell.border = thin_border
            if c_idx in (2, 3, 4):
                cell.alignment = align_right
            elif c_idx == 5:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

        curr_row += 1

    # Section 3: Inspection Type Channel Breakdown
    curr_row += 2
    ws1.cell(row=curr_row, column=1, value="Inspection Mode Breakdown").font = font_section
    curr_row += 1

    type_headers = ["Inspection Mode", "Total Processed", "Defects Found", "Pass Rate (%)", "Avg Latency (ms)"]
    ws1.row_dimensions[curr_row].height = 24
    for col_idx, h in enumerate(type_headers, 1):
        cell = ws1.cell(row=curr_row, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_teal
        cell.alignment = align_center
        cell.border = thin_border

    curr_row += 1
    for mode in ["image", "video", "live"]:
        mode_rows = [r for r in inspections_data if r["inspection_type"] == mode]
        m_total = len(mode_rows)
        m_defects = sum(1 for r in mode_rows if r["status"] == "DEFECT")
        m_pass_rate = ((m_total - m_defects) / m_total) if m_total > 0 else 1.0
        m_avg_lat = (sum(r["processing_time"] for r in mode_rows if r["processing_time"]) / m_total) if m_total > 0 else 0.0

        ws1.row_dimensions[curr_row].height = 20
        bg = fill_zebra_2 if curr_row % 2 == 1 else fill_zebra_1
        
        ws1.cell(row=curr_row, column=1, value=f"{mode.upper()} Mode").font = font_bold
        ws1.cell(row=curr_row, column=2, value=m_total).number_format = "#,##0"
        ws1.cell(row=curr_row, column=3, value=m_defects).number_format = "#,##0"
        ws1.cell(row=curr_row, column=4, value=m_pass_rate).number_format = "0.00%"
        ws1.cell(row=curr_row, column=5, value=m_avg_lat).number_format = "0.0"

        for c_idx in range(1, 6):
            cell = ws1.cell(row=curr_row, column=c_idx)
            cell.fill = bg
            cell.border = thin_border
            if c_idx in (2, 3, 4, 5):
                cell.alignment = align_right
            else:
                cell.alignment = align_left

        curr_row += 1

    # -------------------------------------------------------------
    # SHEET 2: Master_Inspections_Output
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Master_Inspections_Output")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:K2")
    ws2["A1"] = f"MASTER INSPECTION RUNS LOG ({len(inspections_data):,} TOTAL SESSIONS RECORDED)"
    ws2["A1"].font = font_title
    ws2["A1"].fill = fill_navy
    ws2["A1"].alignment = align_center

    headers_insp = [
        "Inspection ID",
        "Mode",
        "Input Filename / Stream",
        "Annotated Output Path",
        "Dominant Classification",
        "Confidence",
        "Quality Status",
        "Box Count",
        "Inference (ms)",
        "Timestamp (UTC)",
        "Input Source"
    ]
    
    ws2.row_dimensions[3].height = 26
    for col_idx, h in enumerate(headers_insp, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_blue
        cell.alignment = align_center
        cell.border = thin_border

    for row_idx, r in enumerate(inspections_data, 4):
        ws2.row_dimensions[row_idx].height = 19
        is_defect = r["status"] == "DEFECT"
        bg = fill_zebra_2 if row_idx % 2 == 1 else fill_zebra_1

        ws2.cell(row=row_idx, column=1, value=r["id"]).alignment = align_center
        ws2.cell(row=row_idx, column=2, value=str(r["inspection_type"]).upper()).alignment = align_center
        ws2.cell(row=row_idx, column=3, value=r["original_filename"] or "N/A").alignment = align_left
        ws2.cell(row=row_idx, column=4, value=r["result_filename"] or "N/A").alignment = align_left
        ws2.cell(row=row_idx, column=5, value=r["defect_type"] or "No Defect").alignment = align_left
        
        c_conf = ws2.cell(row=row_idx, column=6, value=r["confidence"] or 0.0)
        c_conf.number_format = "0.00%"
        c_conf.alignment = align_right

        c_status = ws2.cell(row=row_idx, column=7, value=r["status"])
        c_status.alignment = align_center
        c_status.fill = fill_defect if is_defect else fill_good
        c_status.font = font_defect if is_defect else font_good

        ws2.cell(row=row_idx, column=8, value=r["detection_count"]).alignment = align_right
        
        c_lat = ws2.cell(row=row_idx, column=9, value=r["processing_time"] or 0.0)
        c_lat.number_format = "0.0"
        c_lat.alignment = align_right

        ws2.cell(row=row_idx, column=10, value=str(r["timestamp"])[:19]).alignment = align_center
        ws2.cell(row=row_idx, column=11, value=r["source"] or "System").alignment = align_left

        for c_idx in range(1, 12):
            cell = ws2.cell(row=row_idx, column=c_idx)
            if c_idx != 7:
                cell.font = font_body
                cell.fill = bg
            cell.border = thin_border

    # -------------------------------------------------------------
    # SHEET 3: Detailed_Bounding_Boxes
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="Detailed_Bounding_Boxes")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:L2")
    ws3["A1"] = f"DETAILED LOCALIZED DEFECT BOUNDING BOXES ({len(detections_data):,} DETECTIONS)"
    ws3["A1"].font = font_title
    ws3["A1"].fill = fill_navy
    ws3["A1"].alignment = align_center

    headers_det = [
        "Detection ID",
        "Inspection ID",
        "Mode",
        "Defect Class Name",
        "Confidence Score",
        "X1 (Left px)",
        "Y1 (Top px)",
        "X2 (Right px)",
        "Y2 (Bottom px)",
        "Box Width (px)",
        "Box Height (px)",
        "Bounding Area (px^2)"
    ]

    ws3.row_dimensions[3].height = 26
    for col_idx, h in enumerate(headers_det, 1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_blue
        cell.alignment = align_center
        cell.border = thin_border

    for row_idx, r in enumerate(detections_data, 4):
        ws3.row_dimensions[row_idx].height = 19
        bg = fill_zebra_2 if row_idx % 2 == 1 else fill_zebra_1

        ws3.cell(row=row_idx, column=1, value=r["detection_id"]).alignment = align_center
        ws3.cell(row=row_idx, column=2, value=r["inspection_id"]).alignment = align_center
        ws3.cell(row=row_idx, column=3, value=str(r["inspection_type"]).upper()).alignment = align_center
        ws3.cell(row=row_idx, column=4, value=r["class_name"]).alignment = align_left
        
        c_conf = ws3.cell(row=row_idx, column=5, value=r["confidence"])
        c_conf.number_format = "0.00%"
        c_conf.alignment = align_right

        for i, key in enumerate(["x1", "y1", "x2", "y2", "box_width", "box_height", "box_area"], 6):
            c_coord = ws3.cell(row=row_idx, column=i, value=r[key])
            c_coord.number_format = "#,##0.0"
            c_coord.alignment = align_right

        for c_idx in range(1, 13):
            cell = ws3.cell(row=row_idx, column=c_idx)
            cell.font = font_body
            cell.fill = bg
            cell.border = thin_border

    # -------------------------------------------------------------
    # SHEET 4: Model_Confusion_&_Classes
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="Model_Confusion_&_Classes")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:G2")
    ws4["A1"] = "MODEL DEFECT CLASSES SPECIFICATION & RUNTIME THRESHOLDS"
    ws4["A1"].font = font_title
    ws4["A1"].fill = fill_navy
    ws4["A1"].alignment = align_center

    headers_classes = ["Class ID", "Class Identifier", "Display Label", "Quality Status", "Confidence Threshold", "NMS IoU Threshold", "Bounding Box Color (BGR)"]
    ws4.row_dimensions[3].height = 26
    for col_idx, h in enumerate(headers_classes, 1):
        cell = ws4.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_blue
        cell.alignment = align_center
        cell.border = thin_border

    classes_meta = [
        (0, "normal", "Normal / Good Print", "GOOD", 0.50, 0.45, "(40, 180, 40) Emerald Green"),
        (1, "stringing", "Stringing", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
        (2, "warping", "Warping", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
        (3, "layer_shift", "Layer Shift", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
        (4, "under_extrusion", "Under-Extrusion", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
        (5, "over_extrusion", "Over-Extrusion", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
        (6, "spaghetti", "Spaghetti Failure", "DEFECT", 0.50, 0.45, "(0, 0, 220) Crimson Red"),
    ]

    for row_idx, r in enumerate(classes_meta, 4):
        ws4.row_dimensions[row_idx].height = 22
        is_defect = r[3] == "DEFECT"
        bg = fill_zebra_2 if row_idx % 2 == 1 else fill_zebra_1

        ws4.cell(row=row_idx, column=1, value=r[0]).alignment = align_center
        ws4.cell(row=row_idx, column=2, value=r[1]).alignment = align_left
        ws4.cell(row=row_idx, column=3, value=r[2]).alignment = align_left
        
        c_st = ws4.cell(row=row_idx, column=4, value=r[3])
        c_st.alignment = align_center
        c_st.fill = fill_defect if is_defect else fill_good
        c_st.font = font_defect if is_defect else font_good

        c_th = ws4.cell(row=row_idx, column=5, value=r[4])
        c_th.number_format = "0.00"
        c_th.alignment = align_right

        c_iou = ws4.cell(row=row_idx, column=6, value=r[5])
        c_iou.number_format = "0.00"
        c_iou.alignment = align_right

        ws4.cell(row=row_idx, column=7, value=r[6]).alignment = align_left

        for c_idx in range(1, 8):
            cell = ws4.cell(row=row_idx, column=c_idx)
            if c_idx != 4:
                cell.fill = bg
                cell.font = font_body
            cell.border = thin_border

    # Auto-fit columns across all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row <= 2:
                    continue
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 42)

    wb.save(str(output_path))
    print(f"[SUCCESS] Real Output Excel Sheet Generated: {output_path}")
    print(f"Total Master Inspection Records Exported : {len(inspections_data)}")
    print(f"Total Bounding Box Detections Exported  : {len(detections_data)}")
    return output_path


if __name__ == "__main__":
    out_file = generate_inspection_output_excel()
    print(f"\nExecution finished successfully. File ready at: {out_file.name}")
