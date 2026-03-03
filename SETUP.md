# Cardiff Forms - Setup Guide

## Overview
Butetown Link Tunnel Maintenance System - web-based form management for preventive maintenance scheduling.

**Production:** https://cardiff-forms.onrender.com

---

## Option 1: Docker (Recommended - Same environment for everyone)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed

### Setup
```bash
git clone https://github.com/frarolpu/cardiff-forms.git
cd cardiff-forms
docker-compose up
```

Access: http://localhost:5000

**That's it!** No need to install Python, dependencies, or worry about environment differences.

---

## Option 2: Local Python Setup

### Prerequisites
- Python 3.11+ installed
- Git installed

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/frarolpu/cardiff-forms.git
   cd cardiff-forms
   ```

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   python app.py
   ```

5. **Access:**
   - http://localhost:5000

---

## Project Structure

```
cardiff-forms/
├── app.py                    # Flask backend
├── index.html                # Main form UI
├── forms_final.json          # Form definitions (162 forms)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose setup
├── saved_forms/              # Local storage (filesystem)
├── forms/                    # Form generation scripts
└── README.md
```

---

## Key Features

✅ **Web-based Forms**
- 162 maintenance forms with equipment/locations/tasks
- Support for signatures and initials
- Multi-location entries

✅ **PDF Generation**
- Automatic PDF creation with header logo
- Print-friendly formatting

✅ **Data Storage**
- Database: PostgreSQL (production)
- Fallback: Filesystem (local development)
- Dual-mode storage system

✅ **Responsive Design**
- Works on desktop and tablet
- Modern UI with gradient backgrounds
- Real-time form validation

---

## Development Workflow

### Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally**
   ```bash
   # Using Docker
   docker-compose up
   
   # OR local Python
   python app.py
   ```

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

4. **Push to GitHub:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a pull request** on GitHub for review

6. **Merge and deploy** once approved

---

## Deployment to Production (Render)

Changes pushed to `main` branch automatically deploy to Render via webhook.

**Current Production Status:**
- Branch: `main` at https://github.com/frarolpu/cardiff-forms
- Deployment: Automatic on push
- Database: PostgreSQL on Render
- Keep-alive: Prevents 15-minute spin-down on paid tier

---

## Recent Updates (March 3, 2026)

✅ **Data Quality Fix**
- Corrected 147 forms with multiple frequencies → single frequency
- Form 2.36.6 now shows only "3 YEARLY" (previously "WEEKLY" + "3 YEARLY")

✅ **CSS Fixes**
- Fixed duplicate CSS rules in index.html
- Fixed missing closing braces

✅ **Database Integration**
- Filesystem fallback for local development
- PostgreSQL for production

---

## Troubleshooting

### "Port 5000 already in use"
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Docker won't build
```bash
docker-compose down
docker system prune
docker-compose up --build
```

### Git conflicts
Contact the team before merging conflicting branches.

---

## Database Schema

### Forms Storage
- **Production**: PostgreSQL (connection string in DATABASE_URL)
- **Local**: JSON files in `saved_forms/` directory
- **Backup**: `forms_final_backup.json` (auto-created on corrections)

### Form Data Structure
```json
{
  "section": "2.36.6",
  "equipment": "CONTROL/COMM CABLES",
  "drawing_ref": "B8/1 to B8/6",
  "locations": ["WESTBOUND BORE"],
  "frequencies": ["3 YEARLY"],
  "tasks": [
    { "step": "1", "description": "Task description" },
    ...
  ]
}
```

---

## Environment Variables

### Local Development
```bash
# .env (optional, for local use)
FLASK_ENV=development
DATABASE_URL=  # Leave empty to use filesystem
```

### Production (Render)
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
FLASK_ENV=production
```

---

## Support

For issues or questions:
1. Check existing commits in git history
2. Review the conversation summary in this README
3. Create an issue on GitHub

---

**Last Updated:** March 3, 2026
**Maintained by:** Franco Roldan + Team
