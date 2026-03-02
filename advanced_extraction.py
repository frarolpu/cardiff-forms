"""
Analyze Word document structure to understand how frequencies are assigned.
Look for patterns in shading across frequency columns.
"""

import json
import re
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

def analyze_frequency_columns():
    """
    Advanced analysis: Extract form number and scan for shaded frequency columns.
    """
    doc_path = Path("Section 4 Schedule of Reports Word Nuevo.docx")
    
    if not doc_path.exists():
        print(f"ERROR: {doc_path} not found")
        return {}
    
    doc = Document(str(doc_path))
    form_frequencies = {}
    
    # Frequency columns to search for (in order of priority/columns)
    freq_keywords = {
        'WEEKLY': 'WEEKLY',
        'MONTHLY': 'MONTHLY',
        '3 MONTHLY': '3 MONTHLY',
        '6 MONTHLY': '6 MONTHLY',
        'ANNUALLY': 'ANNUALLY',
        '3 YEARLY': '3 YEARLY',
    }
    
    # Priority order (what to select if multiple found)
    priority = ['3 YEARLY', '6 MONTHLY', 'ANNUALLY', '3 MONTHLY', 'MONTHLY', 'WEEKLY']
    
    for table_idx, table in enumerate(doc.tables):
        form_num = None
        has_shading = {}
        
        # Parse table for form number and frequency presence
        table_text = '\n'.join([cell.text for row in table.rows for cell in row.cells])
        
        # Extract form number
        form_match = re.search(r'Section\s+(\d+\.\d+\.\d+)|(\d+\.\d+\.\d+)', table_text)
        if form_match:
            form_num = form_match.group(1) or form_match.group(2)
        
        # Check which frequencies appear with any styling
        for freq_name in freq_keywords.keys():
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip().upper()
                    if freq_name.upper() in cell_text:
                        # Check for shading or styling
                        has_styling = False
                        try:
                            tcPr = cell._element.tcPr
                            if tcPr is not None:
                                shd = tcPr.find(qn('w:shd'))
                                if shd is not None:
                                    fill = shd.get(qn('w:fill'))
                                    # Non-white background or auto indicates styling
                                    if fill and fill.upper() not in ['FFFFFF', 'AUTO']:
                                        has_styling = True
                                        has_shading[freq_name] = True
                        except:
                            pass
                        
                        if has_styling:
                            break
        
        if form_num and form_num not in form_frequencies:
            # Select primary frequency
            selected_freq = None
            for p_freq in priority:
                if p_freq in has_shading or p_freq in table_text:
                    selected_freq = p_freq
                    break
            
            if selected_freq:
                form_frequencies[form_num] = selected_freq
                print(f"{form_num}: {selected_freq}")
    
    return form_frequencies

def create_corrections():
    """Compare document extraction with forms_final.json and generate corrections."""
    
    print("Analyzing document structure...\n")
    doc_freqs = analyze_frequency_columns()
    
    # Load current forms
    with open('forms_final.json', 'r', encoding='utf-8') as f:
        forms = json.load(f)
    
    corrections = {}
    matches = 0
    mismatches = 0
    
    for form in forms:
        form_num = form['section']
        current_freqs = form.get('frequencies', [])
        
        # Check if this form has multiple frequencies (error case)
        if len(current_freqs) > 1 and form_num in doc_freqs:
            doc_freq = doc_freqs[form_num]
            if doc_freq not in current_freqs:
                # Document has frequency not in current
                corrections[form_num] = doc_freq
                mismatches += 1
            else:
                # Document frequency is one of the current ones
                # Select it as the primary
                corrections[form_num] = doc_freq
                matches += 1
    
    # For forms with multiple frequencies but not in doc, take the most common frequency
    for form in forms:
        form_num = form['section']
        current_freqs = form.get('frequencies', [])
        
        if len(current_freqs) > 1 and form_num not in corrections:
            # No document data, use heuristic - pick last/most specific frequency
            priority = ['3 YEARLY', '6 MONTHLY', 'ANNUALLY', '3 MONTHLY', 'MONTHLY', 'WEEKLY']
            for p_freq in priority:
                if p_freq in current_freqs:
                    corrections[form_num] = [p_freq]
                    break
    
    print(f"\n\nExtracted {len(doc_freqs)} forms from document")
    print(f"Found {len(corrections)} forms needing correction")
    print(f"Document provided guidance for: {matches + mismatches}")
    
    if corrections:
        with open('frequency_corrections.json', 'w', encoding='utf-8') as f:
            json.dump(corrections, f, indent=2)
        print("\n✓ Corrections saved to frequency_corrections.json")

if __name__ == "__main__":
    create_corrections()
