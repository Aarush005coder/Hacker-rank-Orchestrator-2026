# src/evidence_parser.py
import os
import json
import PyPDF2
import pytesseract
from PIL import Image
from .utils import BASE_DIR, load_csv

class EvidenceParser:
    def __init__(self):
        self.evidence_manifest = load_csv("evidence_files.csv")
        self.parsed_cache = {}

    def extract_for_identities(self, identities):
        extracted = {}
        search_terms = list(identities.get('emails', [])) + list(identities.get('user_ids', [])) + list(identities.get('phones', [])) + list(identities.get('hashes', []))
        search_terms = [str(t).lower() for t in search_terms if t]
        
        for _, row in self.evidence_manifest.iterrows():
            # Robustly handle both 'file_id'/'evidence_id' and 'file_path'/'filename'
            file_id = str(row.get('file_id', row.get('evidence_id', 'unknown')))
            file_path = str(row.get('file_path', row.get('filename', '')))
            
            if not file_path or file_path == 'nan':
                continue
                
            filepath = os.path.join(BASE_DIR, file_path)
            if not os.path.exists(filepath):
                filepath = os.path.join(BASE_DIR, "dataset", file_path)
                if not os.path.exists(filepath):
                    continue
                
            if file_id not in self.parsed_cache:
                self.parsed_cache[file_id] = self._parse_file(filepath, file_path)
                
            content = self.parsed_cache[file_id]
            
            if any(term in content.lower() for term in search_terms):
                extracted[file_id] = content
                
        return extracted

    def _parse_file(self, filepath, filename):
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == '.pdf':
                return self._parse_pdf(filepath)
            elif ext in ['.png', '.jpg', '.jpeg']:
                return self._parse_image(filepath)
            elif ext == '.json':
                return self._parse_json(filepath)
            elif ext in ['.sql', '.txt', '.log', '.csv']:
                return self._parse_text(filepath)
            else:
                return self._parse_text(filepath) # Fallback to text
        except Exception as e:
            return f"[Parse Error: {e}]"

    def _parse_pdf(self, filepath):
        text = ""
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    def _parse_image(self, filepath):
        try:
            img = Image.open(filepath)
            return pytesseract.image_to_string(img)
        except Exception as e:
            return f"[OCR Error: {e}]"

    def _parse_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f))

    def _parse_text(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()