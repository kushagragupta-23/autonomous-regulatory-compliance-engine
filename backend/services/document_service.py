import os
import re
import hashlib
from typing import List, Dict, Any
import pypdf

class DocumentService:
    """Ingests and standardizes tax and regulatory documents (PDF/TXT)."""

    @staticmethod
    def calculate_checksum(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

    @classmethod
    def parse_pdf(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        full_text = []
        chunks = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                clean_page = cls._clean_text(page_text)
                full_text.append(clean_page)

                # Segment into paragraph chunks
                raw_paras = [p.strip() for p in clean_page.split("\n\n") if len(p.strip()) > 40]
                for p_idx, para in enumerate(raw_paras):
                    chunks.append({
                        "chunk_id": f"p{page_idx + 1}_c{p_idx + 1}",
                        "page": page_idx + 1,
                        "text": para,
                        "token_estimate": len(para.split())
                    })

        combined = "\n\n".join(full_text)
        return {
            "source": os.path.basename(file_path),
            "pages": total_pages,
            "checksum": cls.calculate_checksum(combined),
            "full_text": combined,
            "chunks": chunks
        }

    @classmethod
    def parse_text(cls, text_content: str, source_name: str = "direct_input.txt") -> Dict[str, Any]:
        clean_text = cls._clean_text(text_content)
        sections = re.split(r'\n(?=[0-9]+\.|\bSection\b|\bNotification\b|\bCircular\b)', clean_text)
        chunks = []
        for idx, sec in enumerate(sections):
            sec_clean = sec.strip()
            if len(sec_clean) > 20:
                chunks.append({
                    "chunk_id": f"sec_{idx + 1}",
                    "page": 1,
                    "text": sec_clean,
                    "token_estimate": len(sec_clean.split())
                })

        return {
            "source": source_name,
            "pages": 1,
            "checksum": cls.calculate_checksum(clean_text),
            "full_text": clean_text,
            "chunks": chunks
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        # Normalize whitespace and strip recurrent header/footers
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

