"""
Root wrapper for Excel export functionality.
Provides backward compatibility and seamless imports for generate_inspection_output_excel.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.export_excel import (
    generate_master_inspection_excel as generate_inspection_output_excel,
    generate_master_inspection_excel,
    generate_single_inspection_excel,
    DEFAULT_MASTER_PATH as DEFAULT_OUTPUT_PATH,
)

if __name__ == "__main__":
    out_file = generate_master_inspection_excel()
    print(f"[SUCCESS] Excel Export Generated at: {out_file}")
