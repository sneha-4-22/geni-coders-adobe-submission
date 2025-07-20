import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFOutlineExtractor:
    def __init__(self):
        # Common heading patterns and indicators
        self.heading_patterns = [
            # Numbers with dots: 1. 1.1 1.1.1
            r'^(\d+\.(?:\d+\.)*)\s*(.+)$',
            # Roman numerals: I. II. III.
            r'^([IVX]+\.)\s*(.+)$',
            # Letters: A. B. C.
            r'^([A-Z]\.)\s*(.+)$',
            # Chapter/Section patterns
            r'^(Chapter|Section|Part)\s+(\d+|[IVX]+|[A-Z])[:\s]*(.+)$',
            # Simple numbering without dots
            r'^(\d+)\s+(.+)$'
        ]
        
        # Keywords that often indicate headings
        self.heading_keywords = [
            'introduction', 'conclusion', 'abstract', 'summary', 'overview',
            'methodology', 'results', 'discussion', 'references', 'bibliography',
            'appendix', 'chapter', 'section', 'background', 'literature review',
            'analysis', 'findings', 'recommendations', 'future work'
        ]

    def extract_title_from_metadata(self, doc) -> Optional[str]:
        """Extract title from PDF metadata"""
        try:
            metadata = doc.metadata
            if metadata.get('title'):
                return metadata['title'].strip()
        except:
            pass
        return None

    def extract_title_from_content(self, doc) -> Optional[str]:
        """Extract title from first page content"""
        try:
            first_page = doc[0]
            blocks = first_page.get_text("dict")["blocks"]
            
            # Look for the largest text on first page (likely title)
            largest_text = ""
            largest_size = 0
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["size"] > largest_size and len(span["text"].strip()) > 5:
                                largest_size = span["size"]
                                largest_text = span["text"].strip()
            
            if largest_text and len(largest_text) < 200:  # Reasonable title length
                return largest_text
                
        except Exception as e:
            logger.warning(f"Error extracting title from content: {e}")
        
        return None

    def is_likely_heading(self, text: str, font_size: float, is_bold: bool, 
                         avg_font_size: float, page_num: int) -> tuple[bool, str]:
        """Determine if text is likely a heading and classify its level"""
        text = text.strip()
        
        if not text or len(text) < 2:
            return False, ""
        
        # Check for numbered patterns
        for pattern in self.heading_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                # Determine level based on pattern complexity
                if '.' in match.group(1):
                    dot_count = match.group(1).count('.')
                    if dot_count == 1:
                        return True, "H1"
                    elif dot_count == 2:
                        return True, "H2"
                    else:
                        return True, "H3"
                else:
                    return True, "H1"
        
        # Font size based classification
        size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1
        
        # Check if it's significantly larger than average
        if size_ratio > 1.3 or is_bold:
            # Additional checks for heading-like properties
            if (len(text) < 100 and  # Not too long
                not text.endswith('.') and  # Doesn't end with period
                len(text.split()) > 1 and  # Has multiple words
                text[0].isupper()):  # Starts with capital
                
                # Classify level based on font size
                if size_ratio > 1.8:
                    return True, "H1"
                elif size_ratio > 1.5:
                    return True, "H2"
                else:
                    return True, "H3"
        
        # Check for common heading keywords
        text_lower = text.lower()
        for keyword in self.heading_keywords:
            if keyword in text_lower:
                if len(text) < 80:  # Reasonable heading length
                    return True, "H1"
        
        return False, ""

    def calculate_average_font_size(self, doc) -> float:
        """Calculate average font size in document"""
        total_size = 0
        count = 0
        
        for page in doc[:min(5, len(doc))]:  # Sample first 5 pages
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                total_size += span["size"]
                                count += 1
        
        return total_size / count if count > 0 else 12

    def extract_outline(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract structured outline from PDF"""
        try:
            doc = fitz.open(pdf_path)
            
            # Try to get title
            title = self.extract_title_from_metadata(doc) or self.extract_title_from_content(doc)
            if not title:
                title = pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
            
            # Calculate average font size
            avg_font_size = self.calculate_average_font_size(doc)
            
            outline = []
            processed_texts = set()  # Avoid duplicates
            
            for page_num, page in enumerate(doc, 1):
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            line_font_size = 0
                            is_bold = False
                            
                            # Combine spans in the same line
                            for span in line["spans"]:
                                if span["text"].strip():
                                    line_text += span["text"]
                                    line_font_size = max(line_font_size, span["size"])
                                    if span["flags"] & 2**4:  # Bold flag
                                        is_bold = True
                            
                            line_text = line_text.strip()
                            
                            # Check if this text is likely a heading
                            if line_text and line_text not in processed_texts:
                                is_heading, level = self.is_likely_heading(
                                    line_text, line_font_size, is_bold, avg_font_size, page_num
                                )
                                
                                if is_heading:
                                    outline.append({
                                        "level": level,
                                        "text": line_text,
                                        "page": page_num
                                    })
                                    processed_texts.add(line_text)
            
            doc.close()
            
            # Sort outline by page number and clean up
            outline.sort(key=lambda x: x["page"])
            
            # Limit to reasonable number of headings
            if len(outline) > 50:
                outline = outline[:50]
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            # Return minimal structure on error
            return {
                "title": pdf_path.stem.replace('_', ' ').replace('-', ' ').title(),
                "outline": []
            }

def process_pdfs():
    """Main processing function"""
    # Get input and output directories
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    extractor = PDFOutlineExtractor()
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file.name}")
        
        try:
            # Extract outline
            result = extractor.extract_outline(pdf_file)
            
            # Create output JSON file
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Processed {pdf_file.name} -> {output_file.name} "
                       f"(found {len(result['outline'])} headings)")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            # Create minimal output file even on error
            error_result = {
                "title": pdf_file.stem.replace('_', ' ').replace('-', ' ').title(),
                "outline": []
            }
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    logger.info("Starting PDF processing")
    process_pdfs()
    logger.info("Completed PDF processing")