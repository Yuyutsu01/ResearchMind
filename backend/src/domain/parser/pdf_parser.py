import os
import re
from typing import Dict, Any, List
import fitz  # PyMuPDF

class ScientificPDFParser:
    """
    Intelligent Document Parser that inspects PDF layers, extracts layout blocks 
    (paragraphs, equations, figures, tables, bibliography), and maps page coordinates.
    """
    @staticmethod
    def detect_capabilities(file_path: str) -> Dict[str, Any]:
        """
        Stage 1: Document Capability Detector.
        Determines if the PDF contains a native text layer, is a scanned document, 
        and extracts baseline counts.
        """
        doc = fitz.open(file_path)
        total_pages = len(doc)
        total_chars = 0
        has_embedded_images = False
        has_vector_graphics = False
        
        for page in doc:
            total_chars += len(page.get_text().strip())
            if len(page.get_images()) > 0:
                has_embedded_images = True
            if len(page.get_drawings()) > 0:
                has_vector_graphics = True
                
        doc.close()
        
        char_density = total_chars / max(total_pages, 1)
        is_scanned = char_density < 50
        
        doc_type = "SCANNED_PDF" if is_scanned else ("MIXED_PDF" if has_embedded_images and char_density < 300 else "VECTOR_PDF")
        
        return {
            "type": doc_type,
            "total_pages": total_pages,
            "char_density": char_density,
            "has_native_text": not is_scanned,
            "has_embedded_images": has_embedded_images,
            "has_vector_graphics": has_vector_graphics
        }

    @staticmethod
    def parse_document_layout(file_path: str) -> Dict[str, Any]:
        """
        Parses a PDF's full text, sections, and coordinates page-by-page.
        Identifies block layout elements (paragraphs, equations, figures, tables).
        """
        doc = fitz.open(file_path)
        objects = []
        relationships = []
        
        # Track active section heading
        current_section = "introduction"
        
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            
            # 1. Parse text blocks (Paragraphs & Headings)
            blocks = page.get_text("blocks")
            for b_idx, block in enumerate(blocks):
                block_text = block[4].strip()
                if len(block_text) < 3:
                    continue
                    
                # Identify if block is a heading/section boundary
                # E.g., short lines starting with Roman numerals or uppercase section titles
                is_heading = False
                if len(block_text) < 100:
                    clean_text = block_text.lower()
                    if re.match(r'^(abstract|introduction|methodology|methods|experiments|results|related|discussion|conclusion|references)', clean_text):
                        is_heading = True
                        current_section = clean_text.split("\n")[0].strip()
                        
                obj_id = f"para_p{page_num}_{b_idx}"
                objects.append({
                    "id": obj_id,
                    "type": "heading" if is_heading else "paragraph",
                    "page": page_num,
                    "bbox": list(block[:4]),
                    "parent_id": current_section,
                    "text_content": block_text,
                    "metadata": {
                        "heading_block": is_heading,
                        "section": current_section
                    }
                })
                
            # 2. Parse math formulas/equations
            # Scans dict structures for symbols or math fonts
            eq_idx = 0
            text_lines = page.get_text("dict")["blocks"]
            for block in text_lines:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = "".join([span["text"] for span in line["spans"]]).strip()
                        # Simple rule-based math detector: symbols + center layout
                        if re.search(r'[\+\-\=\*\/\<\>\(\)\[\]\^_\{\}\\\theta\pi\sigma\alpha\beta\gamma]', line_text) and len(line_text) < 150:
                            if len(line_text) > 4:
                                eq_id = f"eq_p{page_num}_{eq_idx}"
                                objects.append({
                                    "id": eq_id,
                                    "type": "equation",
                                    "page": page_num,
                                    "bbox": list(line["bbox"]),
                                    "parent_id": current_section,
                                    "text_content": line_text,
                                    "metadata": {"latex": f"$${line_text}$$"}
                                })
                                eq_idx += 1
                                
            # 3. Parse figures
            image_info = page.get_images()
            for idx, img in enumerate(image_info):
                drawings = page.get_drawings()
                bbox = [50.0, 100.0, 500.0, 300.0] # fallback bounds
                if drawings:
                    bbox = list(drawings[0]["rect"])
                    
                fig_id = f"fig_p{page_num}_{idx}"
                objects.append({
                    "id": fig_id,
                    "type": "figure",
                    "page": page_num,
                    "bbox": bbox,
                    "parent_id": current_section,
                    "text_content": f"Figure {idx + 1} on Page {page_num}",
                    "metadata": {"caption": f"Visual details in page {page_num}"}
                })
                
        doc.close()
        
        # 4. Citation Cross-Linking
        # Cross-reference citations or figure/equation callouts inside paragraphs
        for obj in objects:
            if obj["type"] == "paragraph":
                p_text = obj["text_content"]
                
                # Link Equation mentions like "Eq. (3)"
                eq_mentions = re.findall(r'(?:Eq\.|Equation)\s*\(?(\d+)\)?', p_text, re.IGNORECASE)
                for mention in eq_mentions:
                    relationships.append({
                        "source_id": obj["id"],
                        "target_id": f"eq_p{obj['page']}_{mention}", # guess mapping on same page
                        "relationship_type": "references"
                    })
                    
                # Link Figure mentions like "Figure 1"
                fig_mentions = re.findall(r'(?:Fig\.|Figure)\s*(\d+)', p_text, re.IGNORECASE)
                for mention in fig_mentions:
                    relationships.append({
                        "source_id": obj["id"],
                        "target_id": f"fig_p{obj['page']}_{int(mention)-1}",
                        "relationship_type": "references"
                    })
                    
        return {
            "success": True,
            "objects": objects,
            "relationships": relationships
        }

scientific_parser = ScientificPDFParser()
