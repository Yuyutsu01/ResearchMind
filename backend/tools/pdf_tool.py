import os
import re
import fitz  # PyMuPDF
import pdfplumber

def extract_pdf_content(pdf_path: str) -> dict:
    """
    Extracts text sections and tables from a research paper PDF.
    Returns a dictionary with structured content.
    """
    if not os.path.exists(pdf_path):
        return {"error": f"File '{pdf_path}' not found."}
        
    result = {
        "title": os.path.basename(pdf_path),
        "raw_text": "",
        "sections": {},
        "tables": [],
        "num_pages": 0
    }
    
    # 1. Extract raw text with PyMuPDF
    try:
        doc = fitz.open(pdf_path)
        result["num_pages"] = len(doc)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        result["raw_text"] = full_text
    except Exception as e:
        return {"error": f"Failed to parse PDF with PyMuPDF: {e}"}
        
    # 2. Parse sections dynamically using Regex
    # Match headers like "1 Introduction", "2. Methodology", "Abstract"
    sections = {
        "abstract": "",
        "introduction": "",
        "methodology": "",
        "results": "",
        "conclusion": "",
        "references": ""
    }
    
    current_section = "introduction"
    lines = result["raw_text"].split("\n")
    
    # Simple regex for finding header candidates
    header_patterns = {
        "abstract": re.compile(r'^\s*(abstract)\s*$', re.IGNORECASE),
        "introduction": re.compile(r'^\s*(\d+(\.\d+)*\s+)?(introduction)\s*$', re.IGNORECASE),
        "methodology": re.compile(r'^\s*(\d+(\.\d+)*\s+)?(methodology|methods|proposed\s+approach|model)\s*$', re.IGNORECASE),
        "results": re.compile(r'^\s*(\d+(\.\d+)*\s+)?(results|experiments|evaluation)\s*$', re.IGNORECASE),
        "conclusion": re.compile(r'^\s*(\d+(\.\d+)*\s+)?(conclusion|concluding|discussion)\s*$', re.IGNORECASE),
        "references": re.compile(r'^\s*(references|bibliography)\s*$', re.IGNORECASE)
    }
    
    # Parse text into sections
    for line in lines:
        stripped = line.strip()
        matched_section = None
        for sec_name, pattern in header_patterns.items():
            if pattern.match(stripped):
                matched_section = sec_name
                break
                
        if matched_section:
            current_section = matched_section
        else:
            if current_section:
                sections[current_section] += line + "\n"
                
    result["sections"] = {k: v.strip() for k, v in sections.items() if v.strip()}
    
    # Fallback: if abstract wasn't extracted, try to grab everything before Introduction
    if not result["sections"].get("abstract") and "introduction" in result["sections"]:
        intro_idx = result["raw_text"].lower().find("introduction")
        abstract_idx = result["raw_text"].lower().find("abstract")
        if abstract_idx != -1 and intro_idx != -1 and abstract_idx < intro_idx:
            result["sections"]["abstract"] = result["raw_text"][abstract_idx:intro_idx].strip()
            
    # 3. Extract tables using pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check up to first 10 pages for tables to manage execution time
            for i, page in enumerate(pdf.pages[:10]):
                tables = page.extract_tables()
                for t in tables:
                    # Clean empty columns/rows
                    cleaned_t = [[cell if cell is not None else "" for cell in row] for row in t]
                    if cleaned_t:
                        result["tables"].append({
                            "page": i + 1,
                            "data": cleaned_t
                        })
    except Exception as e:
        print(f"[PDF Tool] Table extraction error: {e}")
        
    return result

def extract_txt_content(filepath: str) -> dict:
    """Helper to read plain text/markdown paper content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "title": os.path.basename(filepath),
            "raw_text": content,
            "sections": {"full_body": content},
            "tables": [],
            "num_pages": 1
        }
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}
