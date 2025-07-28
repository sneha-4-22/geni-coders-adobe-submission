import fitz
import os
import json
import time
import string
import re
from collections import defaultdict, Counter
from datetime import datetime


def is_header_or_footer_block(span, page_height, header_limit=50, footer_limit=50):
    y_position = span["bbox"][1]
    return y_position <= header_limit or y_position >= (page_height - footer_limit)

def is_title_candidate(span, page_number):
    if page_number != 1:
        return False

    text = span['text'].strip()
    if not text or not any(c.isalpha() for c in text):
        return False
    if sum(1 for c in text if c in string.punctuation) / len(text) > 0.6:
        return False
    if re.fullmatch(r'[^A-Za-z0-9؀-ۿऀ-ॿ一-鿿]{3,}', text):
        return False
    lower_text = text.lower()
    if any(domain in lower_text for domain in ["www.", ".com", ".org", ".net"]):
        return False
    if text.isupper() and len(text.split()) <= 5:
        return False

    bbox_width = span['bbox'][2] - span['bbox'][0]
    font_size = span.get("size", 0)
    return font_size >= 10 and bbox_width >= 100

def extract_title_from_first_page(doc):
    potential_titles = []
    first_page = doc[0]
    for block in first_page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if is_title_candidate(span, 1):
                    potential_titles.append({
                        "text": span["text"].strip(),
                        "y": span["bbox"][1],
                        "font_size": span["size"]
                    })

    if not potential_titles:
        return ""

    max_font_size = max(span["font_size"] for span in potential_titles)
    filtered = [s for s in potential_titles if s["font_size"] >= max_font_size - 1]
    filtered.sort(key=lambda s: s["y"])

    seen_texts = set()
    combined_title = []
    for span in filtered:
        text = span["text"]
        if text not in seen_texts:
            combined_title.append(text)
            seen_texts.add(text)

    return " ".join(combined_title)

def is_heading(span, body_font_size, page_height):
    text = span["text"].strip()
    if not text or len(text) < 3:
        return False
    if text.count(" ") > 10 and not text.endswith(":"):
        return False
    if span.get("span_count_on_line", 1) > 6:
        return False
    if span.get("avg_span_width", 100) < 40:
        return False
    if span["font_size"] <= body_font_size:
        return False
    if is_header_or_footer_block(span, page_height):
        return False
    return True

def classify_heading_level(text):
    if re.match(r"^\d+\.\d+\.\d+\s", text):
        return "H3"
    elif re.match(r"^\d+\.\d+\s", text):
        return "H2"
    elif re.match(r"^\d+\s", text):
        return "H1"
    elif text.endswith(":") and len(text.split()) <= 8 and not text[0].islower():
        return "H4"
    return None

def extract_spans_from_page(doc, page_index):
    page = doc[page_index]
    page_height = page.rect.height
    blocks = page.get_text("dict")["blocks"]
    spans_list = []
    font_sizes = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            spans = line["spans"]
            clean_spans = [s["text"].strip() for s in spans if s["text"].strip()]
            span_count = len(clean_spans)
            total_width = sum(s["bbox"][2] - s["bbox"][0] for s in spans)
            avg_width = total_width / span_count if span_count else 100

            for span in spans:
                if is_header_or_footer_block(span, page_height):
                    continue

                span["text"] = span["text"].strip()
                span["font_size"] = span.get("size", 0)
                span["y"] = span["bbox"][1]
                span["page"] = page_index + 1
                span["span_count_on_line"] = span_count
                span["avg_span_width"] = avg_width
                font_sizes.append(span["font_size"])
                spans_list.append(span)

    return spans_list, font_sizes

def map_font_sizes_to_levels(font_sizes):
    if not font_sizes:
        return {}, 0
    most_common_font = Counter(font_sizes).most_common(1)[0][0]
    sorted_sizes = sorted(set(font_sizes), reverse=True)
    heading_sizes = [s for s in sorted_sizes if s > most_common_font + 0.3]

    heading_map = {}
    if len(heading_sizes) >= 1:
        heading_map[heading_sizes[0]] = "H1"
    if len(heading_sizes) >= 2:
        heading_map[heading_sizes[1]] = "H2"
    if len(heading_sizes) >= 3:
        heading_map[heading_sizes[2]] = "H3"

    return heading_map, most_common_font

def extract_outline_from_doc(doc):
    headings = []
    doc_title = extract_title_from_first_page(doc)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_height = page.rect.height

        spans, font_sizes = extract_spans_from_page(doc, page_index)
        heading_level_map, base_font_size = map_font_sizes_to_levels(font_sizes)

        for span in spans:
            if not is_heading(span, base_font_size, page_height):
                continue
            if span["page"] == 1 and span["text"].strip() in doc_title:
                continue

            text = span["text"]
            size = span["font_size"]
            level = classify_heading_level(text)

            if not level and size in heading_level_map:
                level = heading_level_map[size]

            if level:
                headings.append({
                    "level": level,
                    "text": text,
                    "page": span["page"]
                })

    return headings

# Challenge 1B Enhanced Analyzer
class PersonaDrivenAnalyzer:
    def __init__(self):
        self.importance_keywords = {}
        self.section_patterns = [
            r'^(\d+\.?\s+.+)$',  # Numbered sections
            r'^([A-Z][A-Za-z\s]+:)$',  # Title with colon
            r'^([A-Z]{2,}(?:\s+[A-Z]+)*)$',  # ALL CAPS headings
            r'^(\d+\.\d+\.?\s+.+)$',  # Subsections like 2.1
        ]
    
    def setup_persona_keywords(self, persona, job_to_be_done):
        """Setup importance keywords based on persona and job"""
        keywords = defaultdict(list)
        
        # Extract key terms from persona and job
        persona_text = persona.get('role', '').lower()
        job_text = job_to_be_done.get('task', '').lower()
        
        # Travel planner keywords
        if 'travel' in persona_text or 'planner' in persona_text:
            keywords['high'].extend([
                'cities', 'accommodation', 'hotel', 'restaurant', 'attraction', 'transport', 
                'itinerary', 'budget', 'location', 'activity', 'things to do', 'nightlife',
                'entertainment', 'beach', 'coastal', 'adventure', 'guide', 'tips', 'tricks',
                'packing', 'group', 'friends', 'college', 'young', 'travel', 'visit',
                'explore', 'experience', 'must-see', 'recommended', 'popular'
            ])
            
        # Academic/Research personas
        elif any(word in persona_text for word in ['researcher', 'phd', 'academic', 'scientist']):
            keywords['high'].extend([
                'methodology', 'results', 'conclusion', 'abstract', 'literature', 
                'analysis', 'experiment', 'data', 'findings', 'discussion', 'review',
                'benchmarks', 'performance', 'datasets', 'models', 'algorithms'
            ])
            
        # Business/Investment personas
        elif any(word in persona_text for word in ['analyst', 'investment', 'business', 'financial']):
            keywords['high'].extend([
                'revenue', 'profit', 'financial', 'market', 'growth', 'investment', 
                'performance', 'strategy', 'competitive', 'analysis', 'trends',
                'positioning', 'r&d', 'annual', 'reports'
            ])
            
        # Student personas
        elif any(word in persona_text for word in ['student', 'undergraduate', 'learner']):
            keywords['high'].extend([
                'introduction', 'basics', 'fundamentals', 'concepts', 'examples', 
                'practice', 'exercises', 'summary', 'key', 'mechanisms', 'kinetics',
                'exam', 'preparation', 'study'
            ])
            
        # HR Professional
        elif 'hr' in persona_text or 'human resources' in persona_text:
            keywords['high'].extend([
                'form', 'onboarding', 'compliance', 'policy', 'procedure', 
                'document', 'workflow', 'process'
            ])
            
        # Food/Catering
        elif any(word in persona_text for word in ['food', 'contractor', 'chef', 'catering']):
            keywords['high'].extend([
                'recipe', 'ingredient', 'cooking', 'preparation', 'menu', 
                'vegetarian', 'buffet', 'serving'
            ])
        
        # Job-specific keywords from task description
        job_words = re.findall(r'\b\w{3,}\b', job_text)
        keywords['medium'].extend([word.lower() for word in job_words if len(word) > 3])
        
        self.importance_keywords = dict(keywords)
    
    def extract_enhanced_sections_from_doc(self, doc, doc_name):
        """Extract sections using Challenge 1A logic + enhanced text extraction"""
        # Get title using Challenge 1A
        title = extract_title_from_first_page(doc)
        
        sections = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_height = page.rect.height
            spans, font_sizes = extract_spans_from_page(doc, page_num)
            heading_level_map, base_font_size = map_font_sizes_to_levels(font_sizes)
            
            current_section = None
            section_content = []
            
            for span in spans:
                text = span["text"].strip()
                if not text:
                    continue
                
                # Check if this is a heading using Challenge 1A logic
                if is_heading(span, base_font_size, page_height):
                    # Save previous section
                    if current_section and section_content:
                        current_section["content"] = " ".join(section_content)
                        sections.append(current_section)
                    
                    # Start new section
                    level = classify_heading_level(text)
                    if not level and span["font_size"] in heading_level_map:
                        level = heading_level_map[span["font_size"]]
                    
                    current_section = {
                        "document": doc_name,
                        "section_title": text,
                        "page_number": page_num + 1,
                        "font_size": span["font_size"],
                        "level": level or "H1"
                    }
                    section_content = []
                else:
                    # Add to current section content
                    if current_section:
                        section_content.append(text)
                    elif not sections:  # First content without heading
                        current_section = {
                            "document": doc_name,
                            "section_title": f"Introduction - {doc_name.replace('.pdf', '')}",
                            "page_number": page_num + 1,
                            "font_size": base_font_size,
                            "level": "H1"
                        }
                        section_content = [text]
            
            # Don't forget the last section on the page
            if current_section and section_content:
                current_section["content"] = " ".join(section_content)
                sections.append(current_section)
                current_section = None
                section_content = []
        
        return sections, title
    
    def calculate_importance_score(self, section):
        """Calculate importance score based on persona keywords"""
        title = section.get("section_title", "").lower()
        content = section.get("content", "").lower()
        text = title + " " + content
        
        score = 0
        
        # High importance keywords (5x multiplier for title, 3x for content)
        for keyword in self.importance_keywords.get('high', []):
            title_matches = title.count(keyword.lower()) * 5
            content_matches = content.count(keyword.lower()) * 3
            score += title_matches + content_matches
        
        # Medium importance keywords (2x multiplier)
        for keyword in self.importance_keywords.get('medium', []):
            score += text.count(keyword.lower()) * 2
        
        # Content quality bonuses
        content_length = len(content)
        if content_length > 300:
            score += min(content_length / 300, 3)
        
        # Early document position bonus
        page_bonus = max(0, 3 - (section.get("page_number", 1) * 0.2))
        score += page_bonus
        
        # Heading level bonus (H1 > H2 > H3)
        level = section.get("level", "H1")
        if level == "H1":
            score += 2
        elif level == "H2":
            score += 1.5
        elif level == "H3":
            score += 1
        
        return score
    
    def extract_subsections(self, sections, max_subsections=20):
        """Extract diverse subsections from top sections"""
        subsections = []
        doc_coverage = defaultdict(int)
        max_per_doc = 4
        
        for section in sections[:15]:
            if doc_coverage[section["document"]] >= max_per_doc:
                continue
                
            content = section.get("content", "").strip()
            if not content or len(content) < 100:
                continue
            
            # Split content into meaningful chunks
            if '•' in content or re.search(r'\d+\.', content):
                chunks = re.split(r'[•▪◦]|\d+\.', content)
            else:
                # Split by sentences and group
                sentences = re.split(r'[.!?]+', content)
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    if len(current_chunk) + len(sentence) < 400:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            
            # Process chunks
            for chunk in chunks:
                chunk = chunk.strip()
                if len(subsections) >= max_subsections:
                    break
                    
                if len(chunk) > 50 and len(chunk) < 600:
                    subsections.append({
                        "document": section["document"],
                        "refined_text": chunk,
                        "page_number": section["page_number"]
                    })
                    doc_coverage[section["document"]] += 1
            
            if len(subsections) >= max_subsections:
                break
        
        return subsections[:max_subsections]
    
    def process_document_collection(self, input_file_path):
        """Main processing function"""
        # Read input configuration
        with open(input_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        documents = config.get("documents", [])
        persona = config.get("persona", {})
        job_to_be_done = config.get("job_to_be_done", {})
        
        # Setup persona-specific keywords
        self.setup_persona_keywords(persona, job_to_be_done)
        
        all_sections = []
        input_dir = os.path.dirname(input_file_path)
        
        # Process each document
        for doc_info in documents:
            filename = doc_info.get("filename", "")
            pdf_path = os.path.join(input_dir, "PDFs", filename)
            
            if not os.path.exists(pdf_path):
                continue
                
            try:
                doc = fitz.open(pdf_path)
                sections, title = self.extract_enhanced_sections_from_doc(doc, filename)
                
                # Calculate importance scores
                for section in sections:
                    section["importance_score"] = self.calculate_importance_score(section)
                
                all_sections.extend(sections)
                doc.close()
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        
        # Sort sections by importance
        all_sections.sort(key=lambda x: x["importance_score"], reverse=True)
        
        # Prepare extracted sections with diversity
        extracted_sections = []
        seen_titles = set()
        doc_coverage = defaultdict(int)
        max_per_doc = 3
        
        for section in all_sections:
            title = section["section_title"].strip()
            doc_name = section["document"]
            title_lower = title.lower()
            
            # Skip duplicates and enforce diversity
            is_duplicate = any(title_lower in seen.lower() or seen.lower() in title_lower 
                             for seen in seen_titles if len(title_lower) > 10)
            
            if (not is_duplicate and 
                len(title) > 3 and 
                doc_coverage[doc_name] < max_per_doc and
                len(extracted_sections) < 25):
                
                extracted_sections.append({
                    "document": doc_name,
                    "section_title": title,
                    "importance_rank": len(extracted_sections) + 1,
                    "page_number": section["page_number"]
                })
                seen_titles.add(title_lower)
                doc_coverage[doc_name] += 1
                
            if len(extracted_sections) >= 25:
                break
        
        # Generate subsection analysis
        subsection_analysis = self.extract_subsections(all_sections)
        
        # Prepare output
        output = {
            "metadata": {
                "input_documents": [doc["filename"] for doc in documents],
                "persona": persona.get("role", ""),
                "job_to_be_done": job_to_be_done.get("task", ""),
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }
        
        return output

def main():
    """Process all collections in the input directory"""
    analyzer = PersonaDrivenAnalyzer()
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    os.makedirs(output_dir, exist_ok=True)
    start_time = time.time()
    
    # Look for challenge1b_input.json files in subdirectories
    for root, dirs, files in os.walk(input_dir):
        if "challenge1b_input.json" in files:
            input_file = os.path.join(root, "challenge1b_input.json")
            
            try:
                result = analyzer.process_document_collection(input_file)
                
                # Determine output filename based on directory structure
                collection_name = os.path.basename(root)
                output_file = os.path.join(output_dir, f"{collection_name}_output.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                    
                print(f"✅ Processed collection: {collection_name}")
                
            except Exception as e:
                print(f"❌ Error processing {root}: {e}")
                continue
    
    print(f"✅ Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()