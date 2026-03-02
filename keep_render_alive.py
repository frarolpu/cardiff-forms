#!/usr/bin/env python3
"""
Render Keep-Alive Bot
Prevents Render service from spinning down by making periodic requests
"""

import requests
import time
import logging
from datetime import datetime
from pathlib import Path

# Configuration
WEBSITE_URL = "https://cardiff-forms.onrender.com"  # Change to your Render URL
CHECK_INTERVAL = 900  # 15 minutes in seconds
LOG_FILE = Path("C:/TempApp/Cardiff Forms/keep-alive.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def keep_alive():
    """Make periodic requests to prevent Render spin-down"""
    
    logger.info("="*60)
    logger.info("🤖 Render Keep-Alive Bot Started")
    logger.info(f"URL: {WEBSITE_URL}")
    logger.info(f"Check interval: {CHECK_INTERVAL // 60} minutes")
    logger.info("="*60)
    
    request_count = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    while True:
        request_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            logger.info(f"Request #{request_count} to {WEBSITE_URL}...")
            
            start_time = time.time()
            response = requests.get(
                WEBSITE_URL,
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            response_time = int((time.time() - start_time) * 1000)  # Convert to ms
            
            status = response.status_code
            if status == 200:
                logger.info(f"✓ Success - Status {status} - Response: {response_time}ms")
            else:
                logger.warning(f"⚠ Unexpected status - Status {status} - Response: {response_time}ms")
                
        except requests.exceptions.Timeout:
            logger.error("✗ Timeout - Request took too long")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"✗ Connection Error - {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Request Failed - {str(e)}")
        except Exception as e:
            logger.error(f"✗ Unexpected Error - {str(e)}")
        
        logger.info(f"💤 Sleeping for {CHECK_INTERVAL // 60} minutes until next check...")
        logger.info("-"*60)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        keep_alive()
    except KeyboardInterrupt:
        logger.info("\n🛑 Keep-Alive Bot Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
