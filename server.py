import http.server
import socketserver
import json
import os
import base64
import tempfile
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage
import psycopg2
from psycopg2.extras import RealDictCursor

# Get port from environment or use default
PORT = int(os.environ.get('PORT', 8080))

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', None)
DB_AVAILABLE = DATABASE_URL is not None

# Set working directory (use current directory for flexibility)
if not os.path.exists('forms'):
    os.makedirs('forms', exist_ok=True)

def get_db_connection():
    """Create database connection"""
    if not DB_AVAILABLE:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        return None

def init_db():
    """Initialize database tables"""
    if not DB_AVAILABLE:
        return
    try:
        conn = get_db_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS forms (
                id SERIAL PRIMARY KEY,
                section VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                form_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def generate_pdf(form_data):
    """Generate PDF from form data using ReportLab"""
    try:
        # Create unique filename with timestamp to prevent collisions
        section = form_data.get('section', 'unknown').replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # includes milliseconds
        filename = f"{section}_{timestamp}.pdf"
        filepath = os.path.join('forms', filename)
        print(f"Generating PDF: {filename}")
        
        # Create unique temp file prefix for this submission to avoid conflicts
        temp_prefix = timestamp
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm)
        story = []
        
        # Styles with professional colors matching web version
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#ffffff'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#ffffff'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#0a2463'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        
        # Header with logos

        logo_items = []
        
        # Left: Cardiff Council logo image
        cardiff_logo_path = os.path.join(os.getcwd(), 'Cardiff-Council-Logo.jpg')
        if os.path.exists(cardiff_logo_path):
            try:
                logo_items.append(Image(cardiff_logo_path, width=60*mm, height=40*mm))
            except:
                logo_items.append(Paragraph("Cardiff Council", styles['Normal']))
        else:
            logo_items.append(Paragraph("Cardiff Council", styles['Normal']))
        
        # Right: SICE logo
        sice_logo_path = os.path.join(os.getcwd(), 'SICE-1024x452-1.png')
        if os.path.exists(sice_logo_path):
            try:
                logo_items.append(Image(sice_logo_path, width=60*mm, height=30*mm))
            except:
                logo_items.append(Paragraph("SICE", styles['Normal']))
        else:
            logo_items.append(Paragraph("SICE", styles['Normal']))
        
        # Create header with logos
        header_table = Table([logo_items], colWidths=[85*mm, 85*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6*mm))
        
        # Title section
        title_data = [['MAINTENANCE INSPECTION REPORT']]
        title_table = Table(title_data, colWidths=[170*mm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0a2463')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(title_table)
        story.append(Spacer(1, 8*mm))
        
        # Section details (from form data)
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0a2463'),
            spaceAfter=4,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(f"Section: {form_data.get('section', 'N/A')}", section_title_style))
        
        # Equipment and location info
        info_data = []
        if 'location' in form_data or 'equipment' in form_data:
            if form_data.get('equipment'):
                info_data.append(['Equipment:', form_data.get('equipment', '')])
            if form_data.get('location'):
                info_data.append(['Location:', form_data.get('location', '')])
            if form_data.get('frequency'):
                info_data.append(['Frequency:', form_data.get('frequency', '')])
            if form_data.get('drawing_ref'):
                info_data.append(['Drawing Reference:', form_data.get('drawing_ref', '')])
        
        # Add default basic info if no equipment details
        if not info_data:
            info_data = [
                ['Inspector:', form_data.get('inspector', 'N/A')],
                ['Inspection Date:', form_data.get('inspectionDate', 'N/A')],
                ['Report Generated:', form_data.get('timestamp', 'N/A')[:10] if form_data.get('timestamp') else 'N/A']
            ]
        
        if info_data:
            info_table = Table(info_data, colWidths=[50*mm, 120*mm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0a2463')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#0a2463'))
            ]))
            story.append(info_table)
        
        story.append(Spacer(1, 12*mm))
        
        # Tasks
        story.append(Paragraph("Tasks Performed", section_heading))
        tasks = form_data.get('tasks', [])
        if tasks:
            task_items = []
            for i, task in enumerate(tasks, 1):
                status = '✓' if task.get('completed') else '✗'
                task_items.append(f"{i}. [{status}] {task.get('description', 'N/A')}")
            task_text = '<br/>'.join(task_items)
            story.append(Paragraph(task_text, styles['Normal']))
        else:
            story.append(Paragraph("No tasks recorded", styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # Comments
        story.append(Paragraph("Comments & Observations", section_heading))
        comments = form_data.get('comments', 'No comments')
        story.append(Paragraph(comments if comments else 'No comments', styles['Normal']))
        story.append(Spacer(1, 8*mm))
        
        # Signatures
        story.append(Paragraph("Engineer Information", section_heading))
        eng_data = [
            ['Name:', form_data.get('engineerName', 'N/A')],
            ['Date:', form_data.get('engineerDate', 'N/A')]
        ]
        eng_table = Table(eng_data, colWidths=[40*mm, 120*mm])
        eng_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(eng_table)
        story.append(Spacer(1, 8*mm))
        
        # Supervisor info
        story.append(Paragraph("Supervisor Information", section_heading))
        sup_data = [
            ['Name:', form_data.get('supervisorName', 'N/A')],
            ['Date:', form_data.get('supervisorDate', 'N/A')]
        ]
        sup_table = Table(sup_data, colWidths=[40*mm, 120*mm])
        sup_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(sup_table)
        story.append(Spacer(1, 8*mm))
        
        # Add signatures if they exist
        if form_data.get('signature1') or form_data.get('signature2'):
            story.append(Paragraph("Digital Signatures", section_heading))
            sig_items = []
            
            if form_data.get('signature1'):
                try:
                    sig1_data = form_data['signature1'].split(',')[1]
                    sig1_bytes = base64.b64decode(sig1_data)
                    sig1_path = os.path.join(tempfile.gettempdir(), f'sig1_{temp_prefix}.png')
                    with open(sig1_path, 'wb') as f:
                        f.write(sig1_bytes)
                    if os.path.exists(sig1_path) and os.path.getsize(sig1_path) > 0:
                        sig_items.append(['Engineer Signature', Image(sig1_path, width=60*mm, height=25*mm)])
                    else:
                        sig_items.append(['Engineer Signature', 'No signature'])
                except Exception as e:
                    print(f"Error processing signature 1: {e}")
                    sig_items.append(['Engineer Signature', 'No signature'])
                    
            if form_data.get('signature2'):
                try:
                    sig2_data = form_data['signature2'].split(',')[1]
                    sig2_bytes = base64.b64decode(sig2_data)
                    sig2_path = os.path.join(tempfile.gettempdir(), f'sig2_{temp_prefix}.png')
                    with open(sig2_path, 'wb') as f:
                        f.write(sig2_bytes)
                    if os.path.exists(sig2_path) and os.path.getsize(sig2_path) > 0:
                        sig_items.append(['Supervisor Signature', Image(sig2_path, width=60*mm, height=25*mm)])
                    else:
                        sig_items.append(['Supervisor Signature', 'No signature'])
                except Exception as e:
                    print(f"Error processing signature 2: {e}")
                    sig_items.append(['Supervisor Signature', 'No signature'])
            
            if sig_items:
                sig_table = Table(sig_items, colWidths=[90*mm, 80*mm])
                sig_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                story.append(sig_table)
        
        # Add photos if they exist
        photos = form_data.get('photos', [])
        if photos:
            story.append(PageBreak())
            story.append(Paragraph("Photographic Evidence", section_heading))
            
            photo_items = []
            for i, photo_data in enumerate(photos):
                try:
                    # Decode base64 image
                    img_data = photo_data.split(',')[1]
                    img_bytes = base64.b64decode(img_data)
                    img_path = os.path.join(tempfile.gettempdir(), f'photo_{i}_{temp_prefix}.jpg')
                    
                    with open(img_path, 'wb') as f:
                        f.write(img_bytes)
                    
                    # Check if file was written properly
                    if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                        # Add to story (2 photos per row)
                        if len(photo_items) == 2:
                            photo_table = Table([photo_items], colWidths=[80*mm, 80*mm])
                            photo_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ]))
                            story.append(photo_table)
                            story.append(Spacer(1, 5*mm))
                            photo_items = []
                        
                        photo_items.append(Image(img_path, width=75*mm, height=75*mm))
                        print(f"✓ Added photo {i}: {img_path}")
                    else:
                        print(f"✗ Photo {i} file write failed or is empty")
                except Exception as e:
                    print(f"Error processing photo {i}: {e}")
            
            # Add remaining photos
            if photo_items:
                while len(photo_items) < 2:
                    photo_items.append('N/A')
                photo_table = Table([photo_items], colWidths=[80*mm, 80*mm])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(photo_table)
        
        # Build PDF
        doc.build(story)
        return filepath, filename
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/generate-pdf':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                form_data = json.loads(body.decode('utf-8'))
                
                # Ensure forms directory exists
                os.makedirs('forms', exist_ok=True)
                
                # Generate PDF
                filepath, filename = generate_pdf(form_data)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'filename': filename, 'message': 'PDF generated successfully'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"✅ PDF generated: {filename}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"❌ Error generating PDF: {str(e)}")
                
        elif self.path == '/save-pdf':
            content_length = int(self.headers.get('Content-Length', 0))
            filename = self.headers.get('X-Filename', 'form.pdf')
            
            try:
                body = self.rfile.read(content_length)
                os.makedirs('forms', exist_ok=True)
                filename = filename.replace('\\', '_').replace('/', '_')
                filepath = os.path.join('forms', filename)
                
                with open(filepath, 'wb') as f:
                    f.write(body)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'filename': filename, 'message': 'PDF saved successfully'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"✅ PDF saved: {filename}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"❌ Error saving PDF: {str(e)}")
                
        elif self.path == '/save-form':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                form_data = json.loads(body.decode('utf-8'))
                section = form_data.get('section', 'unknown').replace('.', '_')
                today = datetime.now().strftime('%Y%m%d')
                
                # Save to database if available
                if DB_AVAILABLE:
                    try:
                        conn = get_db_connection()
                        if conn:
                            cur = conn.cursor()
                            cur.execute(
                                'INSERT INTO forms (section, form_data) VALUES (%s, %s)',
                                (form_data.get('section'), json.dumps(form_data))
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print(f"✅ Form saved to database: {section}_{today}")
                    except Exception as db_error:
                        print(f"⚠️ Database save failed: {db_error}, falling back to JSON")
                
                # Also save to JSON as backup
                filename = f"{section}_{today}.json"
                os.makedirs('forms', exist_ok=True)
                filepath = os.path.join('forms', filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, ensure_ascii=False, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'filename': filename, 'message': 'Form saved successfully'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"✅ Form saved: {filename}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"❌ Error saving form: {str(e)}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        # Handle forms viewer page
        if self.path == '/forms-viewer':
            html_content = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cardiff Forms - PDF Viewer</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: Arial, sans-serif; background: #f5f5f5; }
                    header { background: #0a2463; color: white; padding: 20px; text-align: center; }
                    h1 { font-size: 24px; margin-bottom: 5px; }
                    .subtitle { font-size: 14px; opacity: 0.9; }
                    .container { max-width: 1000px; margin: 20px auto; padding: 0 20px; }
                    .file-list { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                    .file-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; transition: background 0.2s; }
                    .file-item:hover { background: #f9f9f9; }
                    .file-item:last-child { border-bottom: none; }
                    .file-info { flex: 1; }
                    .file-name { font-weight: bold; color: #0a2463; margin-bottom: 5px; }
                    .file-size { font-size: 12px; color: #666; }
                    .file-actions { display: flex; gap: 10px; }
                    button { padding: 8px 16px; background: #0a2463; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
                    button:hover { background: #052047; }
                    .no-files { padding: 40px; text-align: center; color: #666; }
                    .stats { margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; text-align: center; }
                    .stats-number { font-size: 24px; font-weight: bold; color: #0a2463; }
                </style>
            </head>
            <body>
                <header>
                    <h1>📋 Cardiff Maintenance Forms</h1>
                    <p class="subtitle">Generated PDF Reports</p>
                </header>
                <div class="container">
                    <div class="stats">
                        <div>Total PDFs Generated: <span class="stats-number" id="count">0</span></div>
                    </div>
                    <div class="file-list" id="fileList">
                        <div class="no-files">Loading...</div>
                    </div>
                </div>
                <script>
                    async function loadFiles() {
                        try {
                            const response = await fetch('/list-forms');
                            const data = await response.json();
                            const fileList = document.getElementById('fileList');
                            const count = document.getElementById('count');
                            
                            count.textContent = data.count;
                            
                            if (data.files.length === 0) {
                                fileList.innerHTML = '<div class="no-files">No PDF forms yet. Submit a form to generate one! 📝</div>';
                                return;
                            }
                            
                            fileList.innerHTML = data.files.map(file => `
                                <div class="file-item">
                                    <div class="file-info">
                                        <div class="file-name">📄 ${file.name}</div>
                                        <div class="file-size">${file.size}</div>
                                    </div>
                                    <div class="file-actions">
                                        <button onclick="window.open('${file.path}', '_blank')">📥 Download</button>
                                    </div>
                                </div>
                            `).join('');
                        } catch (error) {
                            document.getElementById('fileList').innerHTML = '<div class="no-files">Error loading files: ' + error.message + '</div>';
                        }
                    }
                    loadFiles();
                    // Refresh every 5 seconds
                    setInterval(loadFiles, 5000);
                </script>
            </body>
            </html>
            '''
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        
        # Handle file listing API
        elif self.path == '/list-forms':
            try:
                files = []
                if os.path.exists('forms'):
                    for filename in sorted(os.listdir('forms'), reverse=True):
                        filepath = os.path.join('forms', filename)
                        if os.path.isfile(filepath) and filename.endswith('.pdf'):
                            size = os.path.getsize(filepath)
                            files.append({
                                'name': filename,
                                'size': f"{size / 1024:.1f} KB",
                                'path': f'/download-form/{filename}'
                            })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'count': len(files), 'files': files}
                self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        # Handle PDF download
        elif self.path.startswith('/download-form/'):
            try:
                filename = self.path.replace('/download-form/', '')
                filename = filename.split('?')[0]  # Remove query params
                filepath = os.path.join('forms', filename)
                
                if os.path.exists(filepath) and filename.endswith('.pdf'):
                    with open(filepath, 'rb') as f:
                        pdf_content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.send_header('Content-Length', len(pdf_content))
                    self.end_headers()
                    self.wfile.write(pdf_content)
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'status': 'error', 'message': 'File not found'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        else:
            # Serve static files normally
            super().do_GET()

# Initialize database before starting server
if DB_AVAILABLE:
    print("🗄️ Initializing database...")
    init_db()
else:
    print("⚠️ DATABASE_URL not set - using JSON file storage only")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"✅ Servidor iniciado en http://localhost:{PORT}")
    print(f"📋 Abre http://localhost:{PORT} en tu navegador")
    if DB_AVAILABLE:
        print(f"💾 Forms stored in: PostgreSQL Database")
    else:
        print(f"📁 Los formularios completados se guardarán en: c:\\TempApp\\Cardiff Forms\\forms\\")
    print(f"⌨️ Presiona Ctrl+C para detener el servidor")
    httpd.serve_forever()
