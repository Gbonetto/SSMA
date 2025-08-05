import os

root = "C:/Users/grego/Desktop/Dossiers/DisruptIQ/Codes/SSMA"
non_utf8_files = []

for dirpath, _, filenames in os.walk(root):
    for filename in filenames:
        if filename.endswith(('.py', '.txt', '.md', '.csv', '.json')):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    f.read()
            except UnicodeDecodeError:
                non_utf8_files.append(filepath)

print("Fichiers non UTF-8 :")
for f in non_utf8_files:
    print(f)
