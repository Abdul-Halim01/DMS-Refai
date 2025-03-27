import os
import time
import logging
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

def cleanup_pdf_files():
    """Cleanup PDF files older than 1 hour"""
    while True:
        try:
            pdf_dir = 'pdf_reports'
            if os.path.exists(pdf_dir):
                current_time = datetime.now()
                for filename in os.listdir(pdf_dir):
                    file_path = os.path.join(pdf_dir, filename)
                    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if current_time - file_mod_time > timedelta(hours=1):
                        try:
                            os.remove(file_path)
                            logger.debug(f"Removed old PDF file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")
        
        # Sleep for 30 minutes
        time.sleep(30 * 60)

# Start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_pdf_files, daemon=True) 