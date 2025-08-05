import os
import logging
from core.logging import get_logger
from core.file_parser import extract_text_and_metadata
from pipelines.vectorize import store_text_in_qdrant  # Adapté à ta brique vectorisation
import time

# Config
INPUT_DIR = "to_index"    # Dossier où tu mets les fichiers à indexer (personnalisable)
LOG_FILE = "logs/batch_index.log"
SUCCESS_LOG = "logs/batch_success.csv"
ERROR_LOG = "logs/batch_errors.csv"
SUPPORTED_EXT = {"pdf", "docx", "doc", "txt", "xlsx", "xls", "png", "jpg", "jpeg"}

os.makedirs("logs", exist_ok=True)

logger = get_logger(__name__)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

def process_file(path):
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        content = f.read()
    text, meta = extract_text_and_metadata(filename, content)
    if not text or not text.strip():
        raise ValueError("Texte vide ou extraction impossible.")
    nb_chunks = store_text_in_qdrant(text, metadata=meta)
    return nb_chunks, meta

def main():
    total, success, failed = 0, 0, 0
    results = []
    errors = []

    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            ext = file.split(".")[-1].lower()
            if ext not in SUPPORTED_EXT:
                continue
            path = os.path.join(root, file)
            total += 1
            try:
                logger.info("Indexation de : %s", path)
                nb_chunks, meta = process_file(path)
                with open(SUCCESS_LOG, "a", encoding="utf-8") as sl:
                    sl.write(f"{file},{meta['ext']},{nb_chunks}\n")
                logger.info("SUCCESS: %s (%s) -> %d chunks.", file, meta['ext'], nb_chunks)
                success += 1
                results.append((file, meta['ext'], nb_chunks))
            except Exception as e:
                with open(ERROR_LOG, "a", encoding="utf-8") as el:
                    el.write(f"{file},{ext},ERROR,\"{str(e)}\"\n")
                logger.error("FAIL: %s (%s) : %s", file, ext, e)
                failed += 1
                errors.append((file, ext, str(e)))

    # Rapport final
    logger.info("\nIndexation terminée : %d/%d fichiers OK, %d erreurs.", success, total, failed)
    logger.info("Voir : %s, %s, %s", LOG_FILE, SUCCESS_LOG, ERROR_LOG)
    if failed:
        logger.info("Fichiers en erreur : %s", [e[0] for e in errors])
    else:
        logger.info("Aucune erreur.")
    # Possibilité d’envoyer un rapport par email/n8n ici

if __name__ == "__main__":
    t0 = time.time()
    main()
    logger.info("Temps total : %.1f sec", time.time() - t0)
