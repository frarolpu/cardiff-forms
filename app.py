from flask import Flask, request, jsonify, send_from_directory, send_file
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

app = Flask(__name__)

# Create directory for saved forms
SAVED_FORMS_DIR = Path('saved_forms')
SAVED_FORMS_DIR.mkdir(exist_ok=True)

# Error log file
ERROR_LOG = Path('pdf_errors.log')

def log_error(message):
    """Write error to log file"""
    try:
        with open(ERROR_LOG, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

def create_pdf(form_data):
    """Create a PDF from form data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1a1f3a'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#0084ff'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    small_text = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#555')
    )
    
    # Try to add logos
    try:
        logo_elements = []
        cwd = Path.cwd()
        
        # Try Cardiff Council logo (JPG version)
        try:
            logo_path1 = cwd / 'Cardiff-Council-Logo.jpg'
            if logo_path1.exists():
                img1 = Image(str(logo_path1), width=0.8*inch, height=0.6*inch)
                logo_elements.append(img1)
        except Exception as e:
            log_error(f"Cardiff logo error: {e}")
        
        # Try SICE logo
        try:
            logo_path2 = cwd / 'SICE-1024x452-1.png'
            if logo_path2.exists():
                img2 = Image(str(logo_path2), width=1*inch, height=0.4*inch)
                logo_elements.append(img2)
        except Exception as e:
            log_error(f"SICE logo error: {e}")
        
        if logo_elements:
            header_table = Table([logo_elements], colWidths=[2*inch, 2.5*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.2*inch))
    except Exception as e:
        log_error(f"Logo section error: {e}")
    
    # Title
    elements.append(Paragraph(f"Maintenance Form - Section {form_data.get('section', 'N/A')}", title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # General Information
    elements.append(Paragraph("General Information", heading_style))
    
    # Create wrapped text for better fitting
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#333')
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555')
    )
    
    gen_info = [
        ['Section:', str(form_data.get('section', 'N/A'))],
        ['Equipment/System:', str(form_data.get('equipment', 'N/A'))],
        ['Inspector:', str(form_data.get('inspector', 'N/A'))],
        ['Date:', str(form_data.get('inspectionDate', 'N/A'))],
        ['Drawing Reference:', str(form_data.get('drawing_ref', 'N/A'))],
    ]
    
    if form_data.get('locations'):
        locations_text = ', '.join(form_data.get('locations', []))
        gen_info.append(['Locations:', locations_text])
    
    if form_data.get('frequencies'):
        frequencies_text = ', '.join(form_data.get('frequencies', []))
        gen_info.append(['Frequencies:', frequencies_text])
    
    gen_table = Table(gen_info, colWidths=[1.2*inch, 4.3*inch])
    gen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f8f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),

    ]))
    elements.append(gen_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Tasks
    elements.append(Paragraph("Tasks Performed", heading_style))
    tasks = form_data.get('tasks', [])
    if tasks:
        task_data = [
            ['Step', 'Status']
        ]
        for task in tasks:
            status = '✓ Completed' if task.get('completed') else '✗ Not Done'
            task_data.append([
                str(task.get('step', '')),
                status
            ])
        
        task_table = Table(task_data, colWidths=[0.8*inch, 4.7*inch])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0084ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        elements.append(task_table)
        elements.append(Spacer(1, 0.25*inch))
    
    # Comments
    if form_data.get('comments'):
        elements.append(Paragraph("Comments", heading_style))
        comment_style = ParagraphStyle(
            'Comment',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333')
        )
        elements.append(Paragraph(form_data.get('comments', ''), comment_style))
        elements.append(Spacer(1, 0.25*inch))
    
    # Signatures
    elements.append(PageBreak())
    elements.append(Paragraph("Signatures & Authorization", heading_style))
    elements.append(Spacer(1, 0.3*inch))
    
    sig_data = [
        ['Maintenance Engineer', 'Supervisor'],
        [form_data.get('signatures', {}).get('engineer', '_______________'), 
         form_data.get('signatures', {}).get('supervisor', '_______________')],
        [f"Date: {form_data.get('signatures', {}).get('engineerDate', '')}", 
         f"Date: {form_data.get('signatures', {}).get('supervisorDate', '')}"],
    ]
    
    sig_table = Table(sig_data, colWidths=[3.25*inch, 3.25*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, 1), 50),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
    ]))
    elements.append(sig_table)
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    footer_style = ParagraphStyle('footer', parent=styles['Normal'], fontSize=7, textColor=colors.grey)
    elements.append(Paragraph(footer_text, footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/api/save-form', methods=['POST'])
def save_form():
    try:
        data = request.json
        
        # Create filename with timestamp and section number
        section = data.get('section', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{section}_{timestamp}.pdf"
        
        try:
            # Generate PDF
            pdf_buffer = create_pdf(data)
            
            filepath = SAVED_FORMS_DIR / filename
            
            # Save PDF file
            with open(filepath, 'wb') as f:
                f.write(pdf_buffer.getvalue())
        except Exception as e:
            import traceback
            error_msg = f"PDF generation error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            print(error_msg, file=sys.stderr)
            # If PDF fails, still save as JSON
            filename = f"{section}_{timestamp}.json"
        
        # Also save JSON metadata for quick reference
        json_filename = f"{section}_{timestamp}.json"
        json_filepath = SAVED_FORMS_DIR / json_filename
        with open(json_filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Form {section} saved successfully',
            'filename': filename
        }), 200
    
    except Exception as e:
        print(f"Save error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/saved-forms', methods=['GET'])
def get_saved_forms():
    try:
        saved_forms = []
        
        # Get only PDF files, sorted by date (newest first)
        for file in sorted(SAVED_FORMS_DIR.glob('*.pdf'), reverse=True):
            # Try to get metadata from JSON file
            json_file = file.with_suffix('.json')
            if json_file.exists():
                with open(json_file, 'r') as f:
                    form_data = json.load(f)
                    saved_forms.append({
                        'filename': file.name,
                        'section': form_data.get('section', 'N/A'),
                        'equipment': form_data.get('equipment', 'N/A'),
                        'inspector': form_data.get('inspector', 'N/A'),
                        'inspectionDate': form_data.get('inspectionDate', 'N/A')
                    })
        
        return jsonify({
            'success': True,
            'forms': saved_forms,
            'count': len(saved_forms)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/download-form/<filename>', methods=['GET'])
def download_form(filename):
    try:
        filepath = SAVED_FORMS_DIR / filename
        
        if not filepath.exists():
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
