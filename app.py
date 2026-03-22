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
try:
    from PIL import Image as PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False

def resize_image_bytes(img_bytes, max_w=1920, quality=82):
    """Resize image bytes so width <= max_w. Returns JPEG bytes. Falls back to original on error."""
    if not _PILLOW_AVAILABLE:
        return img_bytes
    try:
        buf = BytesIO(img_bytes)
        pil = PILImage.open(buf)
        pil = pil.convert('RGB')  # drop alpha channel (PNG etc.)
        w, h = pil.size
        if w > max_w:
            new_h = int(h * max_w / w)
            pil = pil.resize((max_w, new_h), PILImage.LANCZOS)
        out = BytesIO()
        pil.save(out, format='JPEG', quality=quality, optimize=True)
        return out.getvalue()
    except Exception:
        return img_bytes

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as EmailEncoders

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB hard limit

@app.errorhandler(413)
def request_too_large(e):
    return jsonify({'success': False, 'message': 'Payload too large. Please reduce the number or size of photos.'}), 413

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

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_DATABASE = DATABASE_URL is not None and len(DATABASE_URL) > 0

def get_db_connection():
    """Get database connection"""
    if not USE_DATABASE:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        log_error(f"Database connection error: {str(e)}")
        return None

# ── Email notification (Gmail SMTP) ──────────────────────────────────────────
GMAIL_USER      = os.environ.get('GMAIL_USER', '')
GMAIL_APP_PASS  = os.environ.get('GMAIL_APP_PASSWORD', '')
REPORT_EMAIL_TO = os.environ.get('REPORT_EMAIL_TO', '')

def send_completion_email(form_data, pdf_bytes, filename):
    """Send completed report by email via Gmail SMTP."""
    if not GMAIL_USER or not GMAIL_APP_PASS or not REPORT_EMAIL_TO:
        log_error('Email skipped: Gmail not configured (GMAIL_USER / GMAIL_APP_PASSWORD / REPORT_EMAIL_TO missing)')
        return
    try:
        section    = form_data.get('section', 'N/A')
        equipment  = form_data.get('equipment', 'N/A')
        sigs       = form_data.get('signatures', {})
        engineer   = sigs.get('engineer', 'N/A')
        supervisor = sigs.get('supervisor', 'N/A')
        council    = sigs.get('council', 'N/A')
        insp_date  = form_data.get('inspectionDate', 'N/A')

        msg = MIMEMultipart()
        msg['From']    = f'Cardiff Forms <{GMAIL_USER}>'
        msg['To']      = REPORT_EMAIL_TO
        msg['Subject'] = f'Completed Report – Section {section} – {insp_date}'

        body = (
            f'Completed Maintenance Report – Section {section}\n'
            f'Equipment:      {equipment}\n'
            f'Inspection Date:{insp_date}\n'
            f'Engineer:       {engineer}\n'
            f'Supervisor:     {supervisor}\n'
            f'Council:        {council}\n\n'
            f'The signed report is attached as a PDF.'
        )
        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        EmailEncoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, REPORT_EMAIL_TO, msg.as_string())

        log_error(f'Completion email sent for {filename} to {REPORT_EMAIL_TO}')
    except Exception as e:
        log_error(f'Email send error: {str(e)}')
# ─────────────────────────────────────────────────────────────────────────────

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
                status VARCHAR(20) DEFAULT 'complete',
                pdf_data BYTEA,
                form_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add pin column if it doesn't exist (safe to run multiple times)
        cursor.execute('''
            ALTER TABLE saved_forms ADD COLUMN IF NOT EXISTS pin VARCHAR(20)
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
        
        # Use Unicode font for better character support (especially special symbols like €)
        try:
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
            default_font = 'DejaVu'
        except Exception as font_err:
            log_error(f"Could not load DejaVu font, using Arial: {font_err}")
            default_font = 'Arial'
        
        # Function to sanitize text for Arial font (remove problematic Unicode chars)
        def sanitize_text(text):
            if not text:
                return text
            # Replace common problematic Unicode characters
            replacements = {
                '€': 'EUR',  # Euro symbol
                '£': 'GBP',  # Pound symbol
                '¥': 'JPY',  # Yen symbol
                '©': '(C)',  # Copyright
                '®': '(R)',  # Registered
                '™': '(TM)', # Trademark
            }
            result = str(text)
            for char, replacement in replacements.items():
                result = result.replace(char, replacement)
            # Remove other problematic Unicode characters if using Arial
            if default_font == 'Arial':
                result = result.encode('ascii', 'ignore').decode('ascii')
            return result
        
        # Add header logo image (centered)
        try:
            # Image dimensions: width=150mm, height will scale proportionally
            logo_path = Path('Logos Combined.jpg')
            if logo_path.exists():
                # Center the image
                page_width = pdf.w
                img_width = 150
                left_margin = (page_width - img_width) / 2
                pdf.image(str(logo_path), x=left_margin, w=img_width)
                pdf.ln(15)  # Add space after logo
        except Exception as e:
            log_error(f"Logo image error: {str(e)}")
        
        pdf.set_font(default_font, "B", 16)
        
        # Initialize temp file list for photos
        temp_files = []
        
        # Title
        section = form_data.get('section', 'N/A')
        pdf.cell(0, 10, f"Maintenance Form - Section {section}", 0, 1, "C")
        pdf.set_font(default_font, "", 11)
        pdf.ln(5)
        
        # General Information
        pdf.set_font(default_font, "B", 12)
        pdf.cell(0, 10, "General Information", 0, 1)
        pdf.set_font(default_font, "", 10)
        
        # Create info lines
        info_items = [
            ("Section:", sanitize_text(form_data.get('section', ''))),
            ("Equipment/System:", sanitize_text(form_data.get('equipment', ''))),
            ("Inspector:", sanitize_text(form_data.get('inspector', ''))),
            ("Date:", sanitize_text(form_data.get('inspectionDate', ''))),
            ("Drawing Reference:", sanitize_text(form_data.get('drawing_ref', ''))),
        ]
        
        # Add EDP if this is a matrix form
        if form_data.get('edp'):
            info_items.insert(3, ("EDP:", form_data.get('edp', '')))
        
        if form_data.get('locations'):
            info_items.append(("Locations:", ', '.join(form_data.get('locations', []))))
        
        if form_data.get('frequencies'):
            info_items.append(("Frequencies:", ', '.join(form_data.get('frequencies', []))))
        
        # Set column widths using effective page width
        col1_width = 50
        col2_width = pdf.epw - col1_width - 2
        
        for label, value in info_items:
            pdf.set_font(default_font, "B", 9)
            pdf.cell(col1_width, 7, label, 0, 0)
            pdf.set_font(default_font, "", 9)
            pdf.multi_cell(col2_width, 7, str(value)[:100])
            pdf.ln(2)
        
        pdf.ln(5)
        
        # Tasks
        tasks = form_data.get('tasks', [])
        if tasks:
            pdf.set_font(default_font, "B", 12)
            pdf.cell(0, 10, "Tasks Performed", 0, 1)
            pdf.set_font(default_font, "", 9)
            
            # Use effective page width for task text wrapping
            available_width = pdf.epw - 2
            
            for task in tasks:
                description = sanitize_text(str(task.get('description', task.get('step', ''))))
                step_num = task.get('step', '')
                subtasks = task.get('subtasks')
                if subtasks:
                    # Parent task label (bold, no checkbox)
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font(default_font, "B", 9)
                    pdf.multi_cell(available_width, 6, f"{step_num}. {description}", align='L')
                    pdf.set_font(default_font, "", 9)
                    # Subtasks (indented, with checkbox)
                    for subtask in subtasks:
                        checkbox = 'X' if subtask.get('completed') else '_'
                        sub_text = sanitize_text(str(subtask.get('description', '')))
                        pdf.set_x(pdf.l_margin + 8)
                        pdf.multi_cell(available_width - 8, 6, f"  [{checkbox}] {sub_text}", align='L')
                else:
                    # Regular task with checkbox
                    checkbox = 'X' if task.get('completed') else '_'
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(available_width, 6, f"[{checkbox}] {description}", align='L')
            
            pdf.ln(1)
        
        # Comments - Engineer, Supervisor, and Council sections
        engineer_comments = sanitize_text(form_data.get('engineer_comments') or form_data.get('comments', ''))
        supervisor_comments = sanitize_text(form_data.get('supervisor_comments', ''))
        council_comments = sanitize_text(form_data.get('council_comments', ''))
        materials_used = sanitize_text(form_data.get('materials_used', ''))
        
        if engineer_comments or supervisor_comments or council_comments:
            pdf.ln(3)
            
            # Engineer Comments
            if engineer_comments:
                pdf.set_font(default_font, "B", 12)
                pdf.cell(0, 10, "Maintenance Engineer Comments", 0, 1)
                pdf.set_font(default_font, "", 9)
                eng_comments_text = str(engineer_comments)[:300]
                pdf.multi_cell(0, 7, eng_comments_text)
                pdf.ln(3)
            
            # Supervisor Comments
            if supervisor_comments:
                pdf.set_font(default_font, "B", 12)
                pdf.cell(0, 10, "Contractor Supervisor Comments", 0, 1)
                pdf.set_font(default_font, "", 9)
                sup_comments_text = str(supervisor_comments)[:300]
                pdf.multi_cell(0, 7, sup_comments_text)
                pdf.ln(3)
            
            # Council Comments
            if council_comments:
                pdf.set_font(default_font, "B", 12)
                pdf.cell(0, 10, "Council Approval Comments", 0, 1)
                pdf.set_font(default_font, "", 9)
                council_comments_text = str(council_comments)[:300]
                pdf.multi_cell(0, 7, council_comments_text)
                pdf.ln(3)
        
        # Materials Used section
        if materials_used:
            pdf.set_font(default_font, "B", 12)
            pdf.cell(0, 10, "Materials Used", 0, 1)
            pdf.set_font(default_font, "", 9)
            materials_text = str(materials_used)[:500]
            pdf.multi_cell(0, 7, materials_text)
            pdf.ln(3)
        
        # BEFORE and AFTER Photos sections
        before_photos = form_data.get('beforePhotos', [])
        after_photos = form_data.get('afterPhotos', [])
        has_before = before_photos and len(before_photos) > 0
        has_after = after_photos and len(after_photos) > 0
        
        # BEFORE Inspection Photos
        if has_before:
            try:
                pdf.ln(3)
                pdf.set_font(default_font, "B", 12)
                pdf.cell(0, 10, "BEFORE Inspection Photos", 0, 1)
                pdf.set_font(default_font, "", 9)

                img_max_w = pdf.w - 20  # full usable width (10mm margins)

                for idx, photo_base64 in enumerate(before_photos):
                    try:
                        # Extract base64 data
                        if isinstance(photo_base64, str) and photo_base64.startswith('data:image'):
                            photo_data = photo_base64.split(',')[1]
                        else:
                            photo_data = photo_base64

                        img_bytes = base64.b64decode(photo_data)
                        img_bytes = resize_image_bytes(img_bytes)  # server-side safety resize
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                            tmp.write(img_bytes)
                            temp_files.append(tmp.name)

                        # Compute proportional height and check for page break
                        img_w = img_max_w
                        img_h = None
                        if _PILLOW_AVAILABLE:
                            try:
                                pil = PILImage.open(tmp.name)
                                orig_w, orig_h = pil.size
                                pil.close()
                                if orig_w > 0:
                                    img_h = img_w * (orig_h / orig_w)
                                    remaining = pdf.h - pdf.get_y() - pdf.b_margin
                                    if img_h > remaining - 10:
                                        pdf.add_page()
                            except Exception:
                                pass

                        # Insert image — omit h so fpdf2 preserves aspect ratio
                        pdf.image(temp_files[-1], x=10, w=img_w)
                        pdf.ln(5)
                    except Exception as e:
                        log_error(f"Before photo insertion error: {e}")
                        pass
            except Exception as e:
                log_error(f"Before photos section error: {e}")
        
        # AFTER Inspection Photos
        if has_after:
            try:
                pdf.ln(3)
                pdf.set_font(default_font, "B", 12)
                pdf.cell(0, 10, "AFTER Inspection Photos", 0, 1)
                pdf.set_font(default_font, "", 9)

                img_max_w = pdf.w - 20  # full usable width (10mm margins)

                for idx, photo_base64 in enumerate(after_photos):
                    try:
                        # Extract base64 data
                        if isinstance(photo_base64, str) and photo_base64.startswith('data:image'):
                            photo_data = photo_base64.split(',')[1]
                        else:
                            photo_data = photo_base64

                        img_bytes = base64.b64decode(photo_data)
                        img_bytes = resize_image_bytes(img_bytes)  # server-side safety resize
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                            tmp.write(img_bytes)
                            temp_files.append(tmp.name)

                        # Compute proportional height and check for page break
                        img_w = img_max_w
                        if _PILLOW_AVAILABLE:
                            try:
                                pil = PILImage.open(tmp.name)
                                orig_w, orig_h = pil.size
                                pil.close()
                                if orig_w > 0:
                                    img_h = img_w * (orig_h / orig_w)
                                    remaining = pdf.h - pdf.get_y() - pdf.b_margin
                                    if img_h > remaining - 10:
                                        pdf.add_page()
                            except Exception:
                                pass

                        # Insert image — omit h so fpdf2 preserves aspect ratio
                        pdf.image(temp_files[-1], x=10, w=img_w)
                        pdf.ln(5)
                    except Exception as e:
                        log_error(f"After photo insertion error: {e}")
                        pass
            except Exception as e:
                log_error(f"After photos section error: {e}")

        if has_before or has_after:
            pdf.add_page()
        
        # Signatures section
        pdf.ln(10)
        pdf.set_font(default_font, "B", 11)
        pdf.cell(0, 10, "Approval", 0, 1)
        pdf.ln(5)
        
        sig_col_width = (pdf.w - 20) / 3
        
        # Names with initials
        pdf.set_font(default_font, "B", 8)
        eng_name = sanitize_text(form_data.get('signatures', {}).get('engineer', ''))
        eng_initials = sanitize_text(form_data.get('signatures', {}).get('engineerInitials', ''))
        sup_name = sanitize_text(form_data.get('signatures', {}).get('supervisor', ''))
        sup_initials = sanitize_text(form_data.get('signatures', {}).get('supervisorInitials', ''))
        council_name = sanitize_text(form_data.get('signatures', {}).get('council', ''))
        council_initials = sanitize_text(form_data.get('signatures', {}).get('councilInitials', ''))
        
        eng_text = f"Engineer: {eng_name}"
        if eng_initials:
            eng_text += f" ({eng_initials})"
        sup_text = f"Supervisor: {sup_name}"
        if sup_initials:
            sup_text += f" ({sup_initials})"
        council_text = f"Council: {council_name}"
        if council_initials:
            council_text += f" ({council_initials})"
            
        pdf.cell(sig_col_width, 6, eng_text, 0, 0)
        pdf.cell(sig_col_width, 6, sup_text, 0, 0)
        pdf.cell(sig_col_width, 6, council_text, 0, 1)
        
        # Dates
        pdf.set_font(default_font, "", 7)
        eng_date = form_data.get('signatures', {}).get('engineerDate', '')
        sup_date = form_data.get('signatures', {}).get('supervisorDate', '')
        council_date = form_data.get('signatures', {}).get('councilDate', '')
        pdf.cell(sig_col_width, 5, f"Date: {eng_date}", 0, 0)
        pdf.cell(sig_col_width, 5, f"Date: {sup_date}", 0, 0)
        pdf.cell(sig_col_width, 5, f"Date: {council_date}", 0, 1)
        
        # Footer
        pdf.ln(10)
        pdf.set_font(default_font, "", 7)
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
        
        # Create filename with timestamp and section number (include EDP if matrix form)
        section = data.get('section', 'unknown')
        edp = data.get('edp')  # Get EDP if present (matrix forms)
        status = data.get('status', 'complete')  # Get status ('pending_supervisor', 'pending_council', or 'complete')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Build filename with status indicator
        # For filenames: pending_supervisor -> _PENDING_SUPERVISOR, pending_council -> _PENDING_COUNCIL, complete -> no suffix
        if status == 'complete':
            status_suffix = ""
        else:
            status_suffix = f"_{status.upper()}"
        
        if edp:
            filename = f"{section}_{edp}_{timestamp}{status_suffix}.pdf"
        else:
            filename = f"{section}_{timestamp}{status_suffix}.pdf"
        
        # Generate PDF
        pdf_buffer = create_pdf(data)
        pdf_data = pdf_buffer.getvalue()
        del pdf_buffer  # free BytesIO immediately — we have the bytes

        # Strip photo blobs from form_data before storing as JSONB:
        # photos are already embedded in pdf_data BYTEA — no need to duplicate them in JSON
        import copy as _copy
        data_for_json = _copy.copy(data)
        data_for_json.pop('beforePhotos', None)
        data_for_json.pop('afterPhotos', None)
        data_for_json.pop('photos', None)
        
        # Always save JSON file for form recovery (works with both DB and filesystem)
        try:
            saved_forms_dir = Path('saved_forms')
            saved_forms_dir.mkdir(exist_ok=True)
            json_filename = filename.replace('.pdf', '.json')
            json_path = saved_forms_dir / json_filename
            with open(json_path, 'w') as f:
                json.dump(data_for_json, f, indent=2)
            log_error(f"Saved form data to: {json_path}")
        except Exception as json_err:
            log_error(f"Warning: Could not save JSON file: {str(json_err)}")
        
        # Send completion email if fully signed off (before save, non-blocking)
        if status == 'complete':
            send_completion_email(data, pdf_data, filename)

        # ── Try to save to database FIRST ────────────────────────────────────
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        'INSERT INTO saved_forms (section, filename, status, pdf_data, form_data) VALUES (%s, %s, %s, %s, %s)',
                        (section, filename, status, pdf_data, json.dumps(data_for_json))
                    )
                    log_error(f"Saved to database: {filename} with status {status}")
                    conn.commit()

                    # ── Only delete old pending rows/files AFTER confirmed DB save ──
                    try:
                        # Delete superseded DB rows for this section.
                        # For matrix forms (edp is set) skip broad section delete — pending_form_id handles
                        # the targeted deletion so we don't accidentally wipe other EDP rows.
                        if status == 'complete' and not edp:
                            cursor.execute(
                                "DELETE FROM saved_forms WHERE section = %s AND status IN ('pending_supervisor', 'pending_council') AND filename != %s",
                                (section, filename)
                            )
                            deleted = cursor.rowcount
                            if deleted:
                                log_error(f"Deleted {deleted} old pending DB rows for section {section}")
                        elif status == 'pending_council' and not edp:
                            cursor.execute(
                                "DELETE FROM saved_forms WHERE section = %s AND status = 'pending_supervisor' AND filename != %s",
                                (section, filename)
                            )
                            deleted = cursor.rowcount
                            if deleted:
                                log_error(f"Deleted {deleted} pending_supervisor DB rows for section {section}")
                        conn.commit()
                    except Exception as cleanup_err:
                        log_error(f"Warning: Could not delete old pending DB rows: {str(cleanup_err)}")

                    # Delete old pending rows (both supervisor and council ids may be set in same session)
                    for _id_field in ['pending_form_id', 'pending_council_form_id']:
                        _row_id = data.get(_id_field)
                        if _row_id:
                            try:
                                cursor.execute("DELETE FROM saved_forms WHERE id = %s", (int(_row_id),))
                                conn.commit()
                                log_error(f"Deleted old pending row {_id_field}={_row_id} after save")
                            except Exception as pf_err:
                                log_error(f"Warning: could not delete old pending row {_row_id}: {pf_err}")

                    # Delete old paused row if this form was resumed from a pause
                    resumed_db_id = data.get('resumed_db_id')
                    if resumed_db_id:
                        try:
                            cursor.execute("DELETE FROM saved_forms WHERE status = 'paused' AND id = %s", (int(resumed_db_id),))
                            conn.commit()
                            log_error(f"Deleted resumed paused row with DB id {resumed_db_id}")
                        except Exception as rp_err:
                            log_error(f"Warning: could not delete resumed paused row: {rp_err}")

                    cursor.close()
                    conn.close()

                    # Clean up filesystem PENDING files only after DB success
                    try:
                        saved_forms_dir = Path('saved_forms')
                        # For matrix forms scope cleanup to this EDP only so other EDPs' files survive
                        glob_prefix = f'{section}_{edp}_' if edp else f'{section}_'
                        if status == 'complete':
                            for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_*.pdf'):
                                f_.unlink(); log_error(f"Deleted PENDING file: {f_.name}")
                            for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_*.json'):
                                f_.unlink(); log_error(f"Deleted PENDING JSON: {f_.name}")
                        elif status == 'pending_council':
                            for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_SUPERVISOR.pdf'):
                                f_.unlink(); log_error(f"Deleted PENDING_SUPERVISOR file: {f_.name}")
                            for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_SUPERVISOR.json'):
                                f_.unlink(); log_error(f"Deleted PENDING_SUPERVISOR JSON: {f_.name}")
                    except Exception as fs_clean_err:
                        log_error(f"Warning: filesystem PENDING cleanup error: {str(fs_clean_err)}")

                    return jsonify({
                        'success': True,
                        'message': f'Form {section} saved successfully as {status}',
                        'filename': filename,
                        'status': status
                    }), 200

                except Exception as e:
                    log_error(f"DATABASE INSERT FAILED — form NOT saved to DB: {str(e)}")
                    try:
                        conn.close()
                    except:
                        pass
                    # Return error to user — do NOT silently fall back to filesystem
                    return jsonify({
                        'success': False,
                        'message': f'Database error — form could not be saved. Please try again. ({str(e)})'
                    }), 500
            else:
                log_error("DATABASE CONNECTION FAILED — form NOT saved")
                return jsonify({
                    'success': False,
                    'message': 'Could not connect to database. Please try again in a moment.'
                }), 500

        # ── No database configured: save to filesystem (local dev only) ──────
        try:
            saved_forms_dir = Path('saved_forms')
            saved_forms_dir.mkdir(exist_ok=True)
            pdf_path = saved_forms_dir / filename
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            log_error(f"WARNING: Saved to filesystem only (no DB) — will be lost on restart: {filename}")

            # Delete old pending files (both supervisor and council ids may be set in same session)
            for _id_field in ['pending_form_id', 'pending_council_form_id']:
                _row_id = data.get(_id_field)
                if _row_id:
                    try:
                        for f_ in saved_forms_dir.glob(f'{_row_id}_PENDING_*.pdf'):
                            f_.unlink(); log_error(f"FS: Deleted old pending file: {f_.name}")
                        for f_ in saved_forms_dir.glob(f'{_row_id}_PENDING_*.json'):
                            f_.unlink(); log_error(f"FS: Deleted old pending JSON: {f_.name}")
                    except Exception as pf_err:
                        log_error(f"FS: Could not delete old pending file {_row_id}: {pf_err}")

            # Clean up old PENDING files on filesystem (same logic as DB path)
            try:
                # For matrix forms scope cleanup to this EDP only so other EDPs' files survive
                glob_prefix = f'{section}_{edp}_' if edp else f'{section}_'
                if status == 'complete' and not edp:
                    for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_*.pdf'):
                        f_.unlink(); log_error(f"FS: Deleted PENDING file: {f_.name}")
                    for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_*.json'):
                        f_.unlink(); log_error(f"FS: Deleted PENDING JSON: {f_.name}")
                elif status == 'pending_council' and not edp:
                    for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_SUPERVISOR.pdf'):
                        if f_.name != filename:
                            f_.unlink(); log_error(f"FS: Deleted PENDING_SUPERVISOR file: {f_.name}")
                    for f_ in saved_forms_dir.glob(f'{glob_prefix}*_PENDING_SUPERVISOR.json'):
                        f_.unlink(); log_error(f"FS: Deleted PENDING_SUPERVISOR JSON: {f_.name}")
            except Exception as fs_clean_err:
                log_error(f"Warning: filesystem cleanup error: {str(fs_clean_err)}")

            return jsonify({
                'success': True,
                'message': f'Form {section} saved successfully as {status}',
                'filename': filename,
                'status': status
            }), 200
        except Exception as e:
            log_error(f"Filesystem save error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error saving form: {str(e)}'
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
        saved_forms = []
        
        # Try database first if configured
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT id, filename, section, status, created_at, form_data FROM saved_forms ORDER BY created_at DESC"
                    )
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    for row in rows:
                        # Extract engineer and supervisor names from form_data JSON
                        engineer_name = 'N/A'
                        supervisor_name = 'N/A'
                        
                        if row['form_data']:
                            try:
                                form_data = json.loads(row['form_data']) if isinstance(row['form_data'], str) else row['form_data']
                                if 'signatures' in form_data:
                                    engineer_name = form_data['signatures'].get('engineer', 'N/A')
                                    supervisor_name = form_data['signatures'].get('supervisor', 'N/A')
                                    council_name = form_data['signatures'].get('council', 'N/A')
                            except:
                                council_name = 'N/A'
                        
                        saved_forms.append({
                            'id': row['id'],
                            'filename': row['filename'],
                            'section': row['section'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'engineer': engineer_name,
                            'supervisor': supervisor_name,
                            'council': council_name
                        })
                    
                    return jsonify({
                        'success': True,
                        'forms': saved_forms,
                        'count': len(saved_forms)
                    }), 200
                except Exception as db_err:
                    log_error(f"Database query error: {str(db_err)}")
        
        # Fallback: read from filesystem
        saved_forms_dir = Path('saved_forms')
        if saved_forms_dir.exists():
            for idx, pdf_file in enumerate(sorted(saved_forms_dir.glob('*.pdf'), reverse=True)):
                # Try to load JSON data for engineer/supervisor/council names
                engineer_name = 'N/A'
                supervisor_name = 'N/A'
                council_name = 'N/A'
                
                json_file = saved_forms_dir / pdf_file.name.replace('.pdf', '.json')
                if json_file.exists():
                    try:
                        with open(json_file, 'r') as f:
                            form_data = json.load(f)
                            if 'signatures' in form_data:
                                engineer_name = form_data['signatures'].get('engineer', 'N/A')
                                supervisor_name = form_data['signatures'].get('supervisor', 'N/A')
                                council_name = form_data['signatures'].get('council', 'N/A')
                    except:
                        pass
                
                saved_forms.append({
                    'id': idx + 1,
                    'filename': pdf_file.name,
                    'section': pdf_file.stem.split('_')[0] if '_' in pdf_file.stem else 'N/A',
                    'created_at': datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat(),
                    'engineer': engineer_name,
                    'supervisor': supervisor_name,
                    'council': council_name
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

@app.route('/api/pending-forms', methods=['GET'])
def get_pending_forms():
    """Get list of pending forms for supervisor signature"""
    try:
        pending_forms = []
        
        # Try database first if configured
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    # Get forms waiting for supervisor signature (pending_supervisor status)
                    cursor.execute(
                        'SELECT id, filename, section, status, created_at FROM saved_forms WHERE status = %s ORDER BY created_at DESC',
                        ('pending_supervisor',)
                    )
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    for row in rows:
                        pending_forms.append({
                            'id': row['id'],
                            'filename': row['filename'],
                            'section': row['section'],
                            'status': row['status'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None
                        })
                    
                    return jsonify({
                        'success': True,
                        'forms': pending_forms,
                        'count': len(pending_forms)
                    }), 200
                except Exception as db_err:
                    log_error(f"Database query error: {str(db_err)}")
        
        # Fallback: read from filesystem (look for files with _PENDING_SUPERVISOR suffix)
        saved_forms_dir = Path('saved_forms')
        if saved_forms_dir.exists():
            for pdf_file in sorted(saved_forms_dir.glob('*_PENDING_SUPERVISOR.pdf'), reverse=True):
                # Remove status suffix from stem to get the base filename as ID
                base_id = pdf_file.stem.replace('_PENDING_SUPERVISOR', '')
                pending_forms.append({
                    'id': base_id,
                    'filename': pdf_file.name,
                    'section': base_id.split('_')[0] if '_' in base_id else 'N/A',
                    'status': 'pending_supervisor',
                    'created_at': datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
                })
        
        return jsonify({
            'success': True,
            'forms': pending_forms,
            'count': len(pending_forms)
        }), 200
    
    except Exception as e:
        log_error(f"Get pending forms error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/load-pending-form/<form_id>', methods=['GET'])
def load_pending_form(form_id):
    """Load pending form data for editing by supervisor or council"""
    try:
        # Try database first if configured
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        'SELECT form_data, filename, status FROM saved_forms WHERE id = %s AND (status = %s OR status = %s)',
                        (int(form_id), 'pending_supervisor', 'pending_council')
                    )
                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if row:
                        raw = row['form_data']
                        form_data = json.loads(raw) if isinstance(raw, str) else raw
                        return jsonify({
                            'success': True,
                            'data': form_data,
                            'filename': row['filename'],
                            'status': row['status']
                        }), 200
                except Exception as db_err:
                    log_error(f"Database query error: {str(db_err)}")
        
        # Fallback: load from filesystem using form_id (filename stem) to locate the correct file
        try:
            saved_forms_dir = Path('saved_forms')
            
            # Search for PENDING_SUPERVISOR or PENDING_COUNCIL JSON files matching the form_id
            for json_file in saved_forms_dir.glob(f'{form_id}_PENDING_*.json'):
                try:
                    with open(json_file, 'r') as f:
                        form_data = json.load(f)
                    return jsonify({
                        'success': True,
                        'data': form_data,
                        'filename': json_file.stem.replace('_PENDING_SUPERVISOR', '').replace('_PENDING_COUNCIL', '') + '.pdf',
                        'status': 'pending_supervisor' if '_PENDING_SUPERVISOR' in json_file.name else 'pending_council'
                    }), 200
                except Exception as read_err:
                    log_error(f"Error reading {json_file}: {read_err}")
                    continue
        except Exception as fs_err:
            log_error(f"Filesystem fallback error: {str(fs_err)}")
        
        return jsonify({
            'success': False,
            'message': 'Form not found'
        }), 404
    
    except Exception as e:
        log_error(f"Load pending form error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/council-forms', methods=['GET'])
def get_council_forms():
    """Get list of pending forms awaiting council signature"""
    try:
        council_forms = []
        
        # Try database first if configured
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        'SELECT id, filename, section, status, created_at FROM saved_forms WHERE status = %s ORDER BY created_at DESC',
                        ('pending_council',)
                    )
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    for row in rows:
                        council_forms.append({
                            'id': row['id'],
                            'filename': row['filename'],
                            'section': row['section'],
                            'status': row['status'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None
                        })
                    
                    return jsonify({
                        'success': True,
                        'forms': council_forms,
                        'count': len(council_forms)
                    }), 200
                except Exception as db_err:
                    log_error(f"Database query error: {str(db_err)}")
        
        # Fallback: read from filesystem (look for files with _PENDING_COUNCIL suffix)
        saved_forms_dir = Path('saved_forms')
        if saved_forms_dir.exists():
            for pdf_file in sorted(saved_forms_dir.glob('*_PENDING_COUNCIL.pdf'), reverse=True):
                # Remove status suffix from stem to get the base filename as ID
                base_id = pdf_file.stem.replace('_PENDING_COUNCIL', '')
                council_forms.append({
                    'id': base_id,
                    'filename': pdf_file.name,
                    'section': base_id.split('_')[0] if '_' in base_id else 'N/A',
                    'status': 'pending_council',
                    'created_at': datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
                })
        
        return jsonify({
            'success': True,
            'forms': council_forms,
            'count': len(council_forms)
        }), 200
    
    except Exception as e:
        log_error(f"Get council forms error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/download-form/<form_identifier>', methods=['GET'])
def download_form(form_identifier):
    try:
        # Try to use as database ID if it's a number
        if form_identifier.isdigit() and USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        'SELECT filename, pdf_data, form_data FROM saved_forms WHERE id = %s',
                        (int(form_identifier),)
                    )
                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if row:
                        if row['pdf_data']:
                            return send_file(
                                BytesIO(bytes(row['pdf_data'])),
                                as_attachment=True,
                                download_name=row['filename'],
                                mimetype='application/pdf'
                            )
                        elif row['form_data']:
                            # Paused form — no stored PDF, generate one on-the-fly
                            pdf_filename = row['filename'].replace('.json', '.pdf')
                            pdf_buffer = create_pdf(row['form_data'])
                            return send_file(
                                pdf_buffer,
                                as_attachment=True,
                                download_name=pdf_filename,
                                mimetype='application/pdf'
                            )
                except Exception as db_err:
                    log_error(f"Database query error: {str(db_err)}")
        
        # Try DB lookup by filename (covers non-numeric identifiers like 2.42.2_..._PENDING_SUPERVISOR.pdf)
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        'SELECT filename, pdf_data, form_data FROM saved_forms WHERE filename = %s',
                        (form_identifier,)
                    )
                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if row:
                        if row['pdf_data']:
                            return send_file(
                                BytesIO(bytes(row['pdf_data'])),
                                as_attachment=True,
                                download_name=row['filename'],
                                mimetype='application/pdf'
                            )
                        elif row['form_data']:
                            # Paused form — no stored PDF, generate one on-the-fly
                            pdf_filename = row['filename'].replace('.json', '.pdf')
                            pdf_buffer = create_pdf(row['form_data'])
                            return send_file(
                                pdf_buffer,
                                as_attachment=True,
                                download_name=pdf_filename,
                                mimetype='application/pdf'
                            )
                except Exception as db_err:
                    log_error(f"Database filename lookup error: {str(db_err)}")

        # Last resort: filesystem (local dev / legacy)
        saved_forms_dir = Path('saved_forms')
        pdf_path = saved_forms_dir / form_identifier
        
        if pdf_path.exists() and pdf_path.suffix == '.pdf':
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=form_identifier,
                mimetype='application/pdf'
            )
        
        return jsonify({'success': False, 'message': 'Form not found'}), 404
    
    except Exception as e:
        log_error(f"Download form error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/pause-form', methods=['POST'])
def pause_form():
    """Save a paused form with PIN for later resumption"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No JSON data provided'}), 400
        
        section = data.get('section', 'unknown')
        pin = data.get('pin', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{section}_{timestamp}_PAUSED_{pin}.json"

        # Embed PIN in form_data so we can retrieve it from DB
        data['pin'] = pin

        # Save to database if available
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # If re-pausing a previously resumed form, delete the old paused row first
                    resumed_db_id = data.get('resumed_db_id')
                    if resumed_db_id:
                        try:
                            cursor.execute("DELETE FROM saved_forms WHERE status = 'paused' AND id = %s", (int(resumed_db_id),))
                        except Exception: pass
                    cursor.execute(
                        'INSERT INTO saved_forms (section, filename, status, form_data, pin) VALUES (%s, %s, %s, %s, %s)',
                        (section, filename, 'paused', json.dumps(data), pin)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    log_error(f"Saved paused form to DB: {filename} PIN: {pin}")
                    return jsonify({'success': True, 'message': f'Form paused with PIN: {pin}', 'pin': pin, 'filename': filename}), 200
                except Exception as db_err:
                    log_error(f"DB error saving paused form: {str(db_err)}")
                    try: conn.close()
                    except: pass
                    return jsonify({'success': False, 'message': f'Database error: {str(db_err)}'}), 500
            else:
                return jsonify({'success': False, 'message': 'Could not connect to database'}), 500

        # Fallback: filesystem (local dev only)
        try:
            saved_forms_dir = Path('saved_forms')
            saved_forms_dir.mkdir(exist_ok=True)
            json_path = saved_forms_dir / filename
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            log_error(f"Saved paused form to filesystem: {json_path} PIN: {pin}")
        except Exception as json_err:
            return jsonify({'success': False, 'message': f'Error saving form: {str(json_err)}'}), 500
        
        return jsonify({'success': True, 'message': f'Form paused with PIN: {pin}', 'pin': pin, 'filename': filename}), 200
    
    except Exception as e:
        log_error(f"Pause form error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/paused-forms', methods=['GET'])
def get_paused_forms():
    """Get list of paused forms with PINs"""
    try:
        paused_forms = []

        # Try database first
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT id, filename, section, pin, created_at FROM saved_forms WHERE status = 'paused' ORDER BY created_at DESC"
                    )
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    for row in rows:
                        paused_forms.append({
                            'id': row['id'],
                            'filename': row['filename'],
                            'section': row['section'],
                            'pin': row['pin'],
                            'status': 'paused',
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None
                        })
                    return jsonify({'success': True, 'forms': paused_forms, 'count': len(paused_forms)}), 200
                except Exception as db_err:
                    log_error(f"DB error getting paused forms: {str(db_err)}")

        # Fallback: filesystem
        saved_forms_dir = Path('saved_forms')
        if saved_forms_dir.exists():
            for json_file in sorted(saved_forms_dir.glob('*_PAUSED_*.json'), reverse=True):
                try:
                    filename_parts = json_file.stem.split('_')
                    pin = filename_parts[-1] if filename_parts else '0000'
                    base_id = json_file.stem.replace(f'_PAUSED_{pin}', '')
                    paused_forms.append({
                        'id': base_id,
                        'filename': json_file.name,
                        'section': base_id.split('_')[0] if '_' in base_id else 'N/A',
                        'pin': pin,
                        'status': 'paused',
                        'created_at': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    log_error(f"Error reading paused form {json_file}: {e}")

        return jsonify({'success': True, 'forms': paused_forms, 'count': len(paused_forms)}), 200

    except Exception as e:
        log_error(f"Get paused forms error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/resume-paused-form/<identifier>', methods=['GET'])
def resume_paused_form(identifier):
    """Load a paused form using DB id (preferred) or PIN (fallback)"""
    try:
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    # Prefer lookup by numeric DB id; fall back to pin column
                    if identifier.isdigit():
                        cursor.execute(
                            "SELECT id, form_data, filename, pin FROM saved_forms WHERE status = 'paused' AND id = %s",
                            (int(identifier),)
                        )
                        row = cursor.fetchone()
                        # If no row by id, try treating it as a PIN
                        if not row:
                            cursor.execute(
                                "SELECT id, form_data, filename, pin FROM saved_forms WHERE status = 'paused' AND pin = %s ORDER BY created_at DESC LIMIT 1",
                                (identifier,)
                            )
                            row = cursor.fetchone()
                    else:
                        cursor.execute(
                            "SELECT id, form_data, filename, pin FROM saved_forms WHERE status = 'paused' AND pin = %s ORDER BY created_at DESC LIMIT 1",
                            (identifier,)
                        )
                        row = cursor.fetchone()
                    if row:
                        raw = row['form_data']
                        form_data = json.loads(raw) if isinstance(raw, str) else raw
                        form_id = row['id']
                        filename = row['filename']
                        pin_val = row['pin'] or ''
                        cursor.close()
                        conn.close()
                        log_error(f"Resumed paused form {filename} (DB id {form_id})")
                        safe_filename = filename
                        if pin_val:
                            safe_filename = safe_filename.replace(f'_PAUSED_{pin_val}', '')
                        safe_filename = safe_filename.replace('.json', '.pdf')
                        return jsonify({
                            'success': True,
                            'data': form_data,
                            'filename': safe_filename,
                            'status': 'paused',
                            'db_id': form_id,
                            'pin': pin_val
                        }), 200
                    cursor.close()
                    conn.close()
                except Exception as db_err:
                    log_error(f"DB error resuming paused form: {str(db_err)}")
                    try: conn.close()
                    except: pass

        # Fallback: filesystem (local dev)
        saved_forms_dir = Path('saved_forms')
        if saved_forms_dir.exists():
            for json_file in saved_forms_dir.glob(f'*_PAUSED_{identifier}.json'):
                try:
                    with open(json_file, 'r') as f:
                        form_data = json.load(f)
                    return jsonify({
                        'success': True,
                        'data': form_data,
                        'filename': json_file.stem.replace(f'_PAUSED_{identifier}', '') + '.pdf',
                        'status': 'paused',
                        'db_id': None,
                        'pin': identifier
                    }), 200
                except Exception as read_err:
                    log_error(f"Error reading paused form: {read_err}")
                    continue

        return jsonify({'success': False, 'message': 'Paused form not found'}), 404

    except Exception as e:
        log_error(f"Resume paused form error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/delete-form/<identifier>', methods=['DELETE'])
def delete_form(identifier):
    """Permanently delete any saved form by DB id or filename (admin use only)"""
    try:
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    if identifier.isdigit():
                        cursor.execute("DELETE FROM saved_forms WHERE id = %s", (int(identifier),))
                    else:
                        cursor.execute("DELETE FROM saved_forms WHERE filename = %s", (identifier,))
                    deleted = cursor.rowcount
                    conn.commit()
                    cursor.close()
                    conn.close()
                    if deleted:
                        log_error(f"Admin deleted form: {identifier}")
                        return jsonify({'success': True, 'message': 'Form deleted'}), 200
                    return jsonify({'success': False, 'message': 'Form not found in database'}), 404
                except Exception as db_err:
                    log_error(f"DB error deleting form: {str(db_err)}")
                    try: conn.close()
                    except: pass
                    return jsonify({'success': False, 'message': str(db_err)}), 500
        # Filesystem fallback — delete by filename
        saved_forms_dir = Path('saved_forms')
        deleted_any = False
        target_pdf = saved_forms_dir / identifier
        target_json = saved_forms_dir / identifier.replace('.pdf', '.json')
        if target_pdf.exists():
            target_pdf.unlink()
            deleted_any = True
        if target_json.exists():
            target_json.unlink()
            deleted_any = True
        if deleted_any:
            log_error(f"Admin deleted form (filesystem): {identifier}")
            return jsonify({'success': True, 'message': 'Form deleted'}), 200
        return jsonify({'success': False, 'message': 'Form not found'}), 404
    except Exception as e:
        log_error(f"Delete form error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/delete-paused-form/<identifier>', methods=['DELETE'])
def delete_paused_form(identifier):
    """Permanently delete a paused form by DB id (preferred) or PIN"""
    try:
        if USE_DATABASE:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    if identifier.isdigit():
                        cursor.execute("DELETE FROM saved_forms WHERE status = 'paused' AND id = %s", (int(identifier),))
                    else:
                        cursor.execute("DELETE FROM saved_forms WHERE status = 'paused' AND pin = %s", (identifier,))
                    deleted = cursor.rowcount
                    conn.commit()
                    cursor.close()
                    conn.close()
                    if deleted:
                        return jsonify({'success': True, 'message': 'Paused form deleted'}), 200
                    return jsonify({'success': False, 'message': 'Paused form not found'}), 404
                except Exception as db_err:
                    log_error(f"DB error deleting paused form: {str(db_err)}")
                    try: conn.close()
                    except: pass
                    return jsonify({'success': False, 'message': str(db_err)}), 500
        # Filesystem fallback
        saved_forms_dir = Path('saved_forms')
        deleted_any = False
        for f_ in saved_forms_dir.glob(f'*_PAUSED_{identifier}.json'):
            f_.unlink(); deleted_any = True
        for f_ in saved_forms_dir.glob(f'*_PAUSED_{identifier}.pdf'):
            f_.unlink()
        if deleted_any:
            return jsonify({'success': True, 'message': 'Paused form deleted'}), 200
        return jsonify({'success': False, 'message': 'Paused form not found'}), 404
    except Exception as e:
        log_error(f"Delete paused form error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/debug', methods=['GET'])
def debug_status():
    """Quick diagnostic: DB connection + row counts"""
    info = {
        'database_url_set': bool(DATABASE_URL),
        'use_database': USE_DATABASE,
        'gmail_configured': bool(GMAIL_USER and GMAIL_APP_PASS),
        'report_email_to': REPORT_EMAIL_TO or '(not set)',
        'db_connected': False,
        'row_counts': {},
        'error': None
    }
    if USE_DATABASE:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT status, COUNT(*) FROM saved_forms GROUP BY status ORDER BY status")
                rows = cursor.fetchall()
                info['db_connected'] = True
                info['row_counts'] = {r[0]: r[1] for r in rows}
                cursor.close()
                conn.close()
            except Exception as e:
                info['error'] = str(e)
        else:
            info['error'] = 'Could not connect to database'
    return jsonify(info), 200


if __name__ == '__main__':
    # Use environment variable to determine if running in production
    is_production = os.environ.get('ENVIRONMENT', '').lower() == 'production'
    port = int(os.environ.get('PORT', 5000))
    debug = not is_production  # Only debug locally
    app.run(debug=debug, host='0.0.0.0', port=port)
