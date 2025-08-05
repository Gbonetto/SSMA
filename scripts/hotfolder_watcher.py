import sys
import os
import time
import logging
from core.logging import get_logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.file_parser import extract_text_and_metadata
from pipelines.vectorize import store_text_in_qdrant

WATCH_DIR = "to_index"
PROCESSED_DIR = os.path.join(WATCH_DIR, "processed")
LOG_FILE = "logs/hotfolder_watcher.log"
SUPPORTED_EXT = {"pdf", "docx", "doc", "txt", "xlsx", "xls", "png", "jpg", "jpeg"}

os.makedirs("logs", exist_ok=True)
os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ENCODING UTF-8 pour les logs !
logger = get_logger(__name__)
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

def safe_move(src, dst):
    base, ext = os.path.splitext(dst)
    counter = 1
    while os.path.exists(dst):
        dst = f"{base}_{counter}{ext}"
        counter += 1
    os.rename(src, dst)

def process_file(path):
    filename = os.path.basename(path)
    if "INDEXED_" in filename or "/processed/" in path.replace("\\", "/"):
        logger.info("Ignoré (déjà traité) : %s", path)
        return

    try:
        with open(path, "rb") as f:
            content = f.read()
        text, meta = extract_text_and_metadata(filename, content)
        if not text or not text.strip():
            raise ValueError("Texte vide ou extraction impossible.")
        nb_chunks = store_text_in_qdrant(text, metadata=meta)
        logger.info("✅ %s (%s) importé (%d chunks)", filename, meta['ext'], nb_chunks)

        new_filename = f"INDEXED_{filename}"
        new_path = os.path.join(PROCESSED_DIR, new_filename)
        safe_move(path, new_path)
        logger.info("Déplacé et renommé : %s", new_path)

    except Exception as e:
        logger.error("Erreur import %s : %s", path, e)

class WatcherHandler(FileSystemEventHandler):
    def on_moved(self, event):
        self.on_created(event)

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if "INDEXED_" in filename or "/processed/" in event.src_path.replace("\\", "/"):
            return
        ext = filename.split(".")[-1].lower()
        if ext not in SUPPORTED_EXT:
            logger.info("Ignoré (format non supporté) : %s", event.src_path)
            return
        try:
            logger.info("Détection nouveau fichier : %s", event.src_path)
            time.sleep(1.0)
            process_file(event.src_path)
        except Exception as e:
            logger.error("Erreur process_file sur %s : %s", event.src_path, e)

if __name__ == "__main__":
    observer = Observer()
    event_handler = WatcherHandler()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    logger.info("👋  Watcher actif sur : %s\nDéposez des fichiers, ils seront indexés, renommés et déplacés dans /processed/ automatiquement !", os.path.abspath(WATCH_DIR))
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
