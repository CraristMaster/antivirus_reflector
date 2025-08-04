import os
import hashlib
from virus_signatures import malware_hashes

def compute_md5(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            while chunk := f.read(4096):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def scan_directory(directory):
    infected_files = []
    for root, _, files in os.walk(directory):
        for name in files:
            file_path = os.path.join(root, name)
            file_hash = compute_md5(file_path)
            if file_hash in malware_hashes:
                infected_files.append(file_path)
    return infected_files
