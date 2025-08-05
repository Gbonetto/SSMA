#!/usr/bin/env python3
import os
import sys

FORBIDDEN = ['\ufeff', '\r', chr(0xC3), chr(0xC2)]

def check_file(path: str) -> bool:
    with open(path, 'rb') as f:
        data = f.read()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        print(f"Non UTF-8 file: {path}")
        return False
    bad = False
    for token in FORBIDDEN:
        if token in text:
            print(f"Forbidden sequence '{token}' in {path}")
            bad = True
    return not bad


def main() -> int:
    ok = True
    for root, _, files in os.walk('.'):
        for fname in files:
            if fname.endswith('.py'):
                path = os.path.join(root, fname)
                if not check_file(path):
                    ok = False
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
