from flask import Flask, request, jsonify, send_from_directory, send_file
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from fpdf import FPDF
from io import BytesIO
import psycopg2
from psycopg2.extras import RealDictCursor
import base64

app = Flask(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

# Error log file
ERROR_LOG = Path('pdf_errors.log')

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        log_error(f"Database connection error: {str(e)}")
        return None

def init_db():
    """Initialize database table for saved forms"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_forms (
                id SERIAL PRIMARY KEY,
                section VARCHAR(50),
                filename VARCHAR(255),
                pdf_data BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Database init error: {str(e)}")
        return False

# Initialize database on startup
init_db()

# Disable caching for development
@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Global error handler for API errors
@app.errorhandler(Exception)
def handle_error(error):
    """Catch any unhandled exceptions and return JSON"""
    # Don't log trivial 404s (like favicon.ico)
    if isinstance(error, Exception) and '404' in str(error):
        return jsonify({
            'success': False,
            'message': 'Not found'
        }), 404
    
    import traceback
    error_msg = f"{type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
    log_error(error_msg)
    print(error_msg, file=sys.stderr)
    
    return jsonify({
        'success': False,
        'message': f'Server error: {str(error)}',
        'error_type': type(error).__name__
    }), 500

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
    """Create a PDF from form data using FPDF with signatures and photos"""
    import base64
    import tempfile
    
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Initialize temp file list for photos
        temp_files = []
        
        # Title
        section = form_data.get('section', 'N/A')
        pdf.cell(0, 10, f"Maintenance Form - Section {section}", 0, 1, "C")
        pdf.set_font("Arial", "", 11)
        pdf.ln(5)
        
        # General Information
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "General Information", 0, 1)
        pdf.set_font("Arial", "", 10)
        
        # Create info lines
        info_items = [
            ("Section:", form_data.get('section', '')),
            ("Equipment/System:", form_data.get('equipment', '')),
            ("Inspector:", form_data.get('inspector', '')),
            ("Date:", form_data.get('inspectionDate', '')),
            ("Drawing Reference:", form_data.get('drawing_ref', '')),
        ]
        
        if form_data.get('locations'):
            info_items.append(("Locations:", ', '.join(form_data.get('locations', []))))
        
        if form_data.get('frequencies'):
            info_items.append(("Frequencies:", ', '.join(form_data.get('frequencies', []))))
        
        # Set column widths
        col1_width = 50
        col2_width = pdf.w - col1_width - 20
        
        for label, value in info_items:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(col1_width, 7, label, 0, 0)
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(col2_width, 7, str(value)[:100])
            pdf.ln(2)
        
        pdf.ln(5)
        
        # Tasks
        tasks = form_data.get('tasks', [])
        if tasks:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Tasks Performed", 0, 1)
            pdf.set_font("Arial", "", 9)
            
            # Set left margin and available width for task text wrapping
            left_margin = pdf.l_margin
            available_width = pdf.w - (left_margin * 2) - 2
            
            for task in tasks:
                # Use checkbox representation
                checkbox = 'X' if task.get('completed') else '_'
                step_text = str(task.get('step', ''))
                # Use multi_cell for text wrapping, aligned left
                pdf.set_x(left_margin)
                pdf.multi_cell(available_width, 6, f"[{checkbox}] {step_text}", align='L')
            
            pdf.ln(1)
        
        # Comments
        if form_data.get('comments'):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Comments", 0, 1)
            pdf.set_font("Arial", "", 9)
            comments = form_data.get('comments', '')[:300]
            pdf.multi_cell(0, 7, comments)
            pdf.ln(3)
        
        # Photos section
        photos = form_data.get('photos', [])
        if photos and len(photos) > 0:
            pdf.ln(3)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Photos", 0, 1)
            pdf.set_font("Arial", "", 9)
            
            # Insert photos
            for idx, photo_base64 in enumerate(photos[:4]):  # Max 4 photos per page
                try:
                    # Extract base64 data
                    if isinstance(photo_base64, str) and photo_base64.startswith('data:image'):
                        photo_data = photo_base64.split(',')[1]
                    else:
                        photo_data = photo_base64
                    
                    # Create temp file
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        tmp.write(base64.b64decode(photo_data))
                        temp_files.append(tmp.name)
                    
                    # Add image to PDF (small size)
                    img_width = 30
                    if idx % 2 == 0 and idx > 0:
                        pdf.ln(40)
                    
                    pdf.image(temp_files[-1], w=img_width, h=30)
                    if (idx + 1) % 2 == 0:
                        pdf.ln(40)
                except Exception as e:
                    log_error(f"Photo insertion error: {e}")
                    pass
        
        # Add page for signatures if we have photos
        if photos and len(photos) > 0:
            pdf.add_page()
        
        # Signatures section
        pdf.ln(10)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, "Approval", 0, 1)
        pdf.ln(5)
        
        sig_col_width = (pdf.w - 20) / 2
        
        # Names with initials
        pdf.set_font("Arial", "B", 9)
        eng_name = form_data.get('signatures', {}).get('engineer', '')
        eng_initials = form_data.get('signatures', {}).get('engineerInitials', '')
        sup_name = form_data.get('signatures', {}).get('supervisor', '')
        sup_initials = form_data.get('signatures', {}).get('supervisorInitials', '')
        
        eng_text = f"Engineer: {eng_name}"
        if eng_initials:
            eng_text += f" ({eng_initials})"
        sup_text = f"Supervisor: {sup_name}"
        if sup_initials:
            sup_text += f" ({sup_initials})"
            
        pdf.cell(sig_col_width, 6, eng_text, 0, 0)
        pdf.cell(sig_col_width, 6, sup_text, 0, 1)
        
        # Dates
        pdf.set_font("Arial", "", 8)
        eng_date = form_data.get('signatures', {}).get('engineerDate', '')
        sup_date = form_data.get('signatures', {}).get('supervisorDate', '')
        pdf.cell(sig_col_width, 5, f"Date: {eng_date}", 0, 0)
        pdf.cell(sig_col_width, 5, f"Date: {sup_date}", 0, 1)
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "", 7)
        generated_text = f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        pdf.cell(0, 5, generated_text, 0, 1, "C")
        
        # Return as buffer
        pdf_bytes = pdf.output()
        
        # Clean up temp files only for photos
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return BytesIO(pdf_bytes)
    except Exception as e:
        log_error(f"PDF generation error: {str(e)}")
        raise

@app.route('/api/save-form', methods=['POST'])
@app.route('/api/save-form', methods=['POST'])
def save_form():
    """Save submitted form as PDF in database"""
    try:
        # Extract request data
        try:
            data = request.json
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No JSON data provided'
                }), 400
        except Exception as e:
            log_error(f"JSON parse error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Invalid JSON: {str(e)}'
            }), 400
        
        # Create filename with timestamp and section number
        section = data.get('section', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{section}_{timestamp}.pdf"
        
        # Generate PDF
        pdf_buffer = create_pdf(data)
        pdf_data = pdf_buffer.getvalue()
        
        # Save to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO saved_forms (section, filename, pdf_data) VALUES (%s, %s, %s)',
                (section, filename, pdf_data)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            # Return success response
            response = jsonify({
                'success': True,
                'message': f'Form {section} saved successfully',
                'filename': filename
            })
            response.status_code = 200
            return response
        except Exception as e:
            log_error(f"Database insert error: {str(e)}")
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Error saving to database: {str(e)}'
            }), 500
    except Exception as e:
        log_error(f"Unexpected save error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/get-saved-forms', methods=['GET'])
def get_saved_forms():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            'SELECT id, filename, section, created_at FROM saved_forms ORDER BY created_at DESC'
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        saved_forms = []
        for row in rows:
            saved_forms.append({
                'id': row['id'],
                'filename': row['filename'],
                'section': row['section'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'equipment': 'N/A',
                'inspector': 'N/A'
            })
        
        return jsonify({
            'success': True,
            'forms': saved_forms,
            'count': len(saved_forms)
        }), 200
    
    except Exception as e:
        log_error(f"Get saved forms error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/download-form/<int:form_id>', methods=['GET'])
def download_form(form_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            'SELECT filename, pdf_data FROM saved_forms WHERE id = %s',
            (form_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'message': 'Form not found'}), 404
        
        # Return PDF file
        return send_file(
            BytesIO(row['pdf_data']),
            as_attachment=True,
            download_name=row['filename'],
            mimetype='application/pdf'
        )
    
    except Exception as e:
        log_error(f"Download form error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Use environment variable to determine if running in production
    is_production = os.environ.get('ENVIRONMENT', '').lower() == 'production'
    port = int(os.environ.get('PORT', 5000))
    debug = not is_production  # Only debug locally
    app.run(debug=debug, host='0.0.0.0', port=port)
