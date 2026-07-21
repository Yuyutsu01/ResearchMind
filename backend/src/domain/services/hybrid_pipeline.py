import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
import httpx
import pytesseract
from PIL import Image
import io

# Optional imports for OCR
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070")

class HybridPipeline:
    def __init__(self):
        # Initialize PaddleOCR if available
        self.ocr_engine = None
        if PaddleOCR:
            try:
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
            except Exception as e:
                print(f"[OCR Init Warning] PaddleOCR failed to start: {e}")

    def detect_capabilities(self, file_path: str) -> Dict[str, Any]:
        """
        Step 1: Document Capability Detector.
        Inspects PDF layout density, font presence, and characters to decide the pipeline.
        """
        print(f"[Detector] Analyzing document capabilities: '{file_path}'...")
        doc = fitz.open(file_path)
        total_pages = len(doc)
        total_chars = 0
        has_embedded_images = False
        has_vector_graphics = False
        
        for page in doc:
            total_chars += len(page.get_text().strip())
            # Check for images
            if len(page.get_images()) > 0:
                has_embedded_images = True
            # Check for drawing commands
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
            "has_embedded_images": has_embedded_images,
            "has_vector_graphics": has_vector_graphics,
            "has_native_text": not is_scanned
        }

    def run_grobid(self, file_path: str) -> Optional[str]:
        """
        Step 4: GROBID Scientific Parser.
        Queries local GROBID service to extract TEI XML document hierarchy.
        """
        print(f"[GROBID] Querying header and fulltext API at {GROBID_URL}...")
        try:
            with open(file_path, "rb") as f:
                files = {"input": f}
                # Request full text processing
                res = httpx.post(
                    f"{GROBID_URL}/api/processFulltextDocument",
                    files=files,
                    timeout=60.0
                )
                if res.status_code == 200:
                    return res.text
                else:
                    print(f"[GROBID Error] Returned status code {res.status_code}")
                    return None
        except Exception as e:
            print(f"[GROBID Error] Failed to contact GROBID service: {e}")
            raise e

    def run_ocr(self, page: fitz.Page) -> Dict[str, Any]:
        """
        Step 5: OCR Fallback.
        Performs optical character recognition using PaddleOCR or Tesseract on scanned pages.
        """
        print(f"[OCR Pipeline] Processing Page #{page.number + 1}...")
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        text_content = ""
        words = []
        
        # Try PaddleOCR first
        if self.ocr_engine:
            try:
                # PaddleOCR expects a numpy array or file path
                # Save temp image for Paddle
                temp_path = f"temp_page_{page.number}.png"
                img.save(temp_path)
                result = self.ocr_engine.ocr(temp_path, cls=True)
                os.remove(temp_path)
                
                if result and result[0]:
                    for line in result[0]:
                        box = line[0]  # [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
                        text = line[1][0]
                        conf = line[1][1]
                        
                        x0 = min(pt[0] for pt in box)
                        y0 = min(pt[1] for pt in box)
                        x1 = max(pt[0] for pt in box)
                        y1 = max(pt[1] for pt in box)
                        
                        text_content += text + " "
                        words.append({
                            "text": text,
                            "bbox": [x0, y0, x1, y1],
                            "confidence": conf
                        })
            except Exception as e:
                print(f"[PaddleOCR Error] OCR failed, falling back to Tesseract: {e}")
                self.ocr_engine = None
                
        # Tesseract fallback
        if not self.ocr_engine:
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    if int(data['conf'][i]) > 30:
                        w_text = data['text'][i].strip()
                        if w_text:
                            x0 = data['left'][i]
                            y0 = data['top'][i]
                            x1 = x0 + data['width'][i]
                            y1 = y0 + data['height'][i]
                            text_content += w_text + " "
                            words.append({
                                "text": w_text,
                                "bbox": [float(x0), float(y0), float(x1), float(y1)],
                                "confidence": float(data['conf'][i]) / 100.0
                            })
            except Exception as e:
                print(f"[Tesseract Error] OCR failed completely: {e}")
                raise e
                
        return {
            "text": text_content.strip(),
            "words": words
        }

    def parse_tei_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parses TEI XML output from GROBID into semantic objects.
        """
        print("[TEI XML Parser] Building semantic objects from XML...")
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        root = ET.fromstring(xml_content)
        
        # Extract title
        title_node = root.find(".//tei:titleStmt/tei:title", ns)
        title = title_node.text if title_node is not None else "Unknown Paper"
        
        sections = []
        citations = []
        figures = []
        tables = []
        
        # Parse sections and paragraphs
        for div in root.findall(".//tei:body/tei:div", ns):
            head = div.find("tei:head", ns)
            section_title = head.text if head is not None else "Untitled Section"
            section_id = f"sec_{section_title.lower().replace(' ', '_')}"
            
            sections.append({
                "id": section_id,
                "type": "section",
                "text": section_title,
                "paragraphs": []
            })
            
            for p in div.findall("tei:p", ns):
                p_text = "".join(p.itertext()).strip()
                sections[-1]["paragraphs"].append(p_text)
                
                # Check for bib references inside paragraphs
                for ref in p.findall("tei:ref[@type='bibr']", ns):
                    ref_text = ref.text or ""
                    target_id = ref.get("target") or ""
                    citations.append({
                        "text": ref_text,
                        "target_id": target_id.replace("#", "")
                    })
        
        # Parse figures
        for fig in root.findall(".//tei:figure", ns):
            fig_id = fig.get("{http://www.w3.org/XML/1998/namespace}id") or "fig"
            fig_type = fig.get("type") or "figure"
            head = fig.find("tei:head", ns)
            label = head.text if head is not None else ""
            desc = fig.find("tei:figDesc", ns)
            caption = "".join(desc.itertext()).strip() if desc is not None else ""
            
            if fig_type == "table":
                tables.append({
                    "id": fig_id,
                    "label": label,
                    "caption": caption
                })
            else:
                figures.append({
                    "id": fig_id,
                    "label": label,
                    "caption": caption
                })
                
        return {
            "title": title,
            "sections": sections,
            "citations": citations,
            "figures": figures,
            "tables": tables
        }

    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Step 10: Semantic Document Builder.
        Combines PDF.js character boxes, PyMuPDF drawing segments, GROBID TEI parser, and OCR pipelines.
        """
        # 1. Detector
        caps = self.detect_capabilities(file_path)
        print(f"[Pipeline] Capability scan: {caps}")
        
        doc = fitz.open(file_path)
        
        semantic_objects = []
        relationships = []
        
        # If it has selectable text, execute primary PDF.js / PyMuPDF + GROBID pipeline
        if caps["has_native_text"]:
            # Run GROBID
            grobid_xml = None
            try:
                grobid_xml = self.run_grobid(file_path)
            except Exception:
                print("[Pipeline Warning] GROBID down. Processing layout locally using PyMuPDF...")
                
            sections_text = {}
            if grobid_xml:
                parsed_tei = self.parse_tei_xml(grobid_xml)
                title = parsed_tei["title"]
                
                # Register paper metadata object
                semantic_objects.append({
                    "id": "doc_metadata",
                    "type": "metadata",
                    "page": 1,
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "text_content": title,
                    "metadata": {
                        "filename": os.path.basename(file_path),
                        "total_pages": len(doc)
                    }
                })
                
                # Append sections
                for sec in parsed_tei["sections"]:
                    sec_text = "\n".join(sec["paragraphs"])
                    sections_text[sec["id"]] = sec_text
                    
                    semantic_objects.append({
                        "id": sec["id"],
                        "type": "section",
                        "page": 1,
                        "bbox": [0.0, 0.0, 0.0, 0.0],
                        "text_content": sec["text"],
                        "metadata": {}
                    })
                    
                    # Store paragraphs
                    for idx, para in enumerate(sec["paragraphs"]):
                        para_id = f"para_{sec['id']}_{idx}"
                        semantic_objects.append({
                            "id": para_id,
                            "type": "paragraph",
                            "page": 1,
                            "bbox": [0.0, 0.0, 0.0, 0.0],
                            "parent_id": sec["id"],
                            "text_content": para,
                            "metadata": {}
                        })
            else:
                # Local layout parser fallback if GROBID down
                title = os.path.basename(file_path)
                for page in doc:
                    text_blocks = page.get_text("blocks")
                    for idx, block in enumerate(text_blocks):
                        block_text = block[4].strip()
                        if len(block_text) > 30:
                            para_id = f"para_p{page.number + 1}_{idx}"
                            semantic_objects.append({
                                "id": para_id,
                                "type": "paragraph",
                                "page": page.number + 1,
                                "bbox": list(block[:4]),
                                "text_content": block_text,
                                "metadata": {}
                            })
                            
            # Process figures, equations, tables using PyMuPDF coordinate scanners
            for page in doc:
                # Find figures / images coordinates
                image_info = page.get_images()
                for idx, img in enumerate(image_info):
                    # Guess location coordinates of the image object
                    rects = page.get_drawings()
                    bbox = [50.0, 100.0, 500.0, 300.0]  # default bounds
                    if rects:
                        bbox = list(rects[0]["rect"])
                        
                    fig_id = f"fig_p{page.number + 1}_{idx}"
                    semantic_objects.append({
                        "id": fig_id,
                        "type": "figure",
                        "page": page.number + 1,
                        "bbox": bbox,
                        "text_content": f"Figure {idx + 1} on Page {page.number + 1}",
                        "metadata": {"caption": f"Visual details in page {page.number + 1}"}
                    })
                
                # Scans text lines to identify Math Formulas
                text_lines = page.get_text("dict")["blocks"]
                eq_idx = 0
                for block in text_lines:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = "".join([span["text"] for span in line["spans"]]).strip()
                            # Match common mathematical symbols or centering offsets
                            if re.search(r'[\+\-\=\*\/\<\>\(\)\[\]\^_\{\}\\\theta\pi\sigma\alpha\beta\gamma]', line_text) and len(line_text) < 150:
                                if len(line_text) > 5:
                                    eq_id = f"eq_p{page.number + 1}_{eq_idx}"
                                    semantic_objects.append({
                                        "id": eq_id,
                                        "type": "equation",
                                        "page": page.number + 1,
                                        "bbox": list(line["bbox"]),
                                        "text_content": line_text,
                                        "metadata": {
                                            "latex": f"$${line_text}$$",
                                            "derivation": "Derived from context methodology."
                                        }
                                    })
                                    eq_idx += 1
                                    
        else:
            # Scanned Document: Run OCR on all pages
            print("[Pipeline] Running OCR parsing pipeline...")
            for page in doc:
                try:
                    ocr_res = self.run_ocr(page)
                    para_id = f"para_ocr_p{page.number + 1}"
                    semantic_objects.append({
                        "id": para_id,
                        "type": "paragraph",
                        "page": page.number + 1,
                        "bbox": [20.0, 20.0, 580.0, 800.0],
                        "text_content": ocr_res["text"],
                        "metadata": {}
                    })
                except Exception as oe:
                    print(f"[Pipeline OCR Error] OCR failed for page {page.number + 1}: {oe}")
                
        doc.close()
        
        # Step 9: Citation Cross-Linking
        # Connect equations/figures to paragraphs that mention them
        for obj in semantic_objects:
            if obj["type"] == "paragraph":
                p_text = obj["text_content"]
                
                # Check for Equation mentions e.g. "Eq. (5)" or "Equation 5"
                eq_mentions = re.findall(r'(?:Eq\.|Equation)\s*\(?(\d+)\)?', p_text, re.IGNORECASE)
                for mention in eq_mentions:
                    relationships.append({
                        "source_id": obj["id"],
                        "target_id": f"eq_p1_{mention}",  # guess mapping
                        "relationship_type": "references"
                    })
                    
                # Check for Figure mentions e.g. "Fig. 3" or "Figure 3"
                fig_mentions = re.findall(r'(?:Fig\.|Figure)\s*(\d+)', p_text, re.IGNORECASE)
                for mention in fig_mentions:
                    relationships.append({
                        "source_id": obj["id"],
                        "target_id": f"fig_p1_{mention}",
                        "relationship_type": "references"
                    })
        
        return {
            "success": True,
            "capabilities": caps,
            "objects": semantic_objects,
            "relationships": relationships
        }

# Singleton Instance
hybrid_pipeline = HybridPipeline()
