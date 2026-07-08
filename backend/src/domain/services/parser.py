import re
import fitz  # PyMuPDF
from typing import Dict, Any

class ScientificParser:
    @staticmethod
    def parse_pdf(file_path: str) -> Dict[str, Any]:
        """Parses a scientific PDF paper using PyMuPDF (fitz) and extracts structured sections."""
        print(f"[PyMuPDF Parser] Extracting content from '{file_path}'...")
        try:
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
                
            # Close doc
            doc.close()
            
            # Simple regular expression section splitter
            sections = {
                "abstract": "",
                "introduction": "",
                "methodology": "",
                "results": "",
                "conclusion": "",
                "references": ""
            }
            
            # Locate section boundaries using standard scientific headings
            text_lower = full_text.lower()
            
            # Helper to find heading index
            def find_idx(patterns: list[str]) -> int:
                for pat in patterns:
                    match = re.search(pat, text_lower)
                    if match:
                        return match.start()
                return -1
                
            abs_idx = find_idx([r'\babstract\b'])
            intro_idx = find_idx([r'\b1\.?\s+introduction\b', r'\bintroduction\b'])
            method_idx = find_idx([r'\bmethodology\b', r'\bmethods\b', r'\b3\.?\s+'])
            results_idx = find_idx([r'\bresults\b', r'\bexperiments\b', r'\b4\.?\s+'])
            conclusion_idx = find_idx([r'\bconclusion\b', r'\bconclusions\b'])
            ref_idx = find_idx([r'\breferences\b', r'\bbibliography\b'])
            
            # Slice text based on indices
            # If abstract exists
            if abs_idx != -1:
                end_abs = intro_idx if intro_idx != -1 else len(full_text)
                sections["abstract"] = full_text[abs_idx:end_abs].strip()
                
            if intro_idx != -1:
                end_intro = method_idx if method_idx != -1 else len(full_text)
                sections["introduction"] = full_text[intro_idx:end_intro].strip()
                
            if method_idx != -1:
                end_method = results_idx if results_idx != -1 else len(full_text)
                sections["methodology"] = full_text[method_idx:end_method].strip()
                
            if results_idx != -1:
                end_results = conclusion_idx if conclusion_idx != -1 else len(full_text)
                sections["results"] = full_text[results_idx:end_results].strip()
                
            if conclusion_idx != -1:
                end_conclusion = ref_idx if ref_idx != -1 else len(full_text)
                sections["conclusion"] = full_text[conclusion_idx:end_conclusion].strip()
                
            if ref_idx != -1:
                sections["references"] = full_text[ref_idx:].strip()
                
            # If splitting failed completely, put all text into abstract
            if not any(sections.values()):
                sections["abstract"] = full_text[:4000]
                sections["introduction"] = full_text[4000:8000]
                
            # Clean section headers
            for k, v in sections.items():
                # Remove repeated whitespace
                sections[k] = re.sub(r'\s+', ' ', v)[:6000]  # Cap length for LLM budget
                
            return {
                "success": True,
                "sections": sections,
                "raw_text": full_text[:30000] # Cap raw text size
            }
        except Exception as e:
            print(f"[PyMuPDF Parser Error] Failed to parse PDF: {e}")
            return {
                "success": False,
                "error": str(e),
                "sections": {}
            }

# Singleton Instance
scientific_parser = ScientificParser()
