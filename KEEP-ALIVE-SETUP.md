# Render Keep-Alive Setup Guide

Your Render service spins down after 15 minutes of inactivity. This bot prevents that by making periodic requests.

## Options:

### Option 1: Quick Start (PowerShell) - Manual
```powershell
cd "C:\TempApp\Cardiff Forms"
powershell -ExecutionPolicy Bypass -File keep-render-alive.ps1
```
Runs directly in PowerShell. Logs to `keep-alive.log`

### Option 2: Python Script (Recommended)
```powershell
cd "C:\TempApp\Cardiff Forms"
venv\Scripts\python keep_render_alive.py
```
More reliable, better error handling.

### Option 3: Batch Launcher (Auto-restart on crash)
```
C:\TempApp\Cardiff Forms\run-keep-alive.bat
```
Keeps the script running even if it crashes.

---

## Setup for Automatic Running (Windows Task Scheduler)

### Method A: Using Batch (Easiest)

1. **Open Task Scheduler:**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task:**
   - Right-click "Task Scheduler Library" → "Create Basic Task"
   - Name: "Keep Render Alive"
   - Description: "Prevents Cardiff Forms from spinning down"
   - Click Next

3. **Trigger (When to run):**
   - Select: "At startup"
   - Click Next

4. **Action (What to run):**
   - Action: "Start a program"
   - Program: `C:\TempApp\Cardiff Forms\run-keep-alive.bat`
   - Click Next

5. **Finish** and enable "Run with highest privileges" if prompted

---

### Method B: Using Python

1. **Open Task Scheduler** (same as above)

2. **Create Basic Task:**
   - Name: "Keep Render Alive (Python)"
   - Trigger: "At startup"

3. **Action:**
   - Program: `C:\TempApp\Cardiff Forms\venv\Scripts\python.exe`
   - Arguments: `keep_render_alive.py`
   - Start in: `C:\TempApp\Cardiff Forms`

4. **Finish**

---

## Monitoring

Check logs to see if bot is working:
```powershell
# Follow live logs
Get-Content "C:\TempApp\Cardiff Forms\keep-alive.log" -Wait

# Or just view file
notepad "C:\TempApp\Cardiff Forms\keep-alive.log"
```

Expected log output:
```
2026-02-24 10:30:45 - INFO - Request #1 to https://cardiff-forms.onrender.com...
2026-02-24 10:30:47 - INFO - ✓ Success - Status 200 - Response: 1234ms
2026-02-24 10:30:47 - INFO - 💤 Sleeping for 15 minutes until next check...
```

---

## Configuration

Edit `keep_render_alive.py` or `keep-render-alive.ps1` to change:

```python
WEBSITE_URL = "https://cardiff-forms.onrender.com"  # Your URL
CHECK_INTERVAL = 900  # 15 minutes (in seconds) - change if needed
```

### Common intervals:
- 5 min = 300 seconds
- 10 min = 600 seconds
- 15 min = 900 seconds (default)

---

## Troubleshooting

**Bot not running after restart?**
- Check Task Scheduler: Right-click task → "Run"
- Check logs for errors
- Verify file paths exist

**High CPU/Memory usage?**
- Increase `CHECK_INTERVAL` (e.g., 1800 = 30 minutes)
- Stop and restart the task

**"Permission Denied" error?**
- Run PowerShell as Administrator
- Or right-click .bat file → "Run as administrator"

**Still spinning down?**
- Render might have a shorter idle timeout on free tier
- Consider upgrading to paid plan
- Or decrease `CHECK_INTERVAL` to 300 (5 minutes)

---

## Alternative: Render Cron Job

For a more permanent solution, you could deploy a separate service on Render that pings your app:
1. Create a simple Node.js / Python service
2. Deploy it to Render (free tier)
3. Add a cron job to ping your main service

Ask if you want help setting that up!
