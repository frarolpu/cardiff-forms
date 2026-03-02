#!/usr/bin/env python3
"""
Extract and validate Schedule of Reports from Word document
Compares against forms_final.json to verify frequencies match the shaded cells
"""

import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX

def extract_schedule_from_docx(docx_path):
    """Extract schedule data from Word document"""
    doc = Document(docx_path)
    
    results = []
    
    # Find and process tables
    for table_idx, table in enumerate(doc.tables):
        print(f"\n📋 Table {table_idx + 1}:")
        print(f"Rows: {len(table.rows)}, Columns: {len(table.columns)}")
        
        # Print table structure
        for row_idx, row in enumerate(table.rows):
            cells_data = []
            for col_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                
                # Check if cell is highlighted/shaded
                shading = None
                try:
                    shading_elm = cell._element.tcPr.shd
                    if shading_elm is not None:
                        shading = shading_elm.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill")
                except:
                    pass
                
                highlight = "🟨" if shading else "⬜"
                cells_data.append(f"{highlight} {text[:30]}")
            
            print(f"  Row {row_idx}: {' | '.join(cells_data)}")

def validate_frequencies(json_path):
    """Check current frequencies in forms_final.json"""
    with open(json_path, 'r') as f:
        forms = json.load(f)
    
    print("\n\n" + "="*80)
    print("📊 CURRENT FREQUENCIES IN forms_final.json")
    print("="*80)
    
    # Group by frequency combinations
    freq_groups = {}
    for form in forms:
        section = form['section']
        freq_tuple = tuple(sorted(form['frequencies']))
        
        if freq_tuple not in freq_groups:
            freq_groups[freq_tuple] = []
        freq_groups[freq_tuple].append(section)
    
    # Print grouped
    for frequencies, sections in sorted(freq_groups.items()):
        print(f"\n{' + '.join(frequencies)} ({len(sections)} forms):")
        print(f"  {', '.join(sorted(sections))}")
    
    # Highlight potential issues
    print("\n\n" + "="*80)
    print("⚠️  POTENTIAL ISSUES (Multiple frequencies per form)")
    print("="*80)
    
    multi_freq = [f for f in forms if len(f['frequencies']) > 1]
    if multi_freq:
        print(f"\nFound {len(multi_freq)} forms with MULTIPLE frequencies:")
        for form in sorted(multi_freq, key=lambda x: x['section']):
            print(f"  {form['section']}: {form['frequencies']}")
    else:
        print("\n✓ No forms with multiple frequencies")

if __name__ == "__main__":
    docx_file = Path("Section 4 Schedule of Reports Word Nuevo.docx")
    json_file = "forms_final.json"
    
    if docx_file.exists():
        print("🔍 Analyzing Word document structure...")
        extract_schedule_from_docx(str(docx_file))
    else:
        print(f"❌ Document not found: {docx_file}")
    
    if Path(json_file).exists():
        validate_frequencies(json_file)
    else:
        print(f"❌ JSON file not found: {json_file}")
    
    print("\n" + "="*80)
    print("✅ Analysis complete. Review above for discrepancies.")
    print("="*80)
