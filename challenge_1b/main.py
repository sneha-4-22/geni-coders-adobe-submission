import fitz
import os
import json
import time
import re
from collections import defaultdict, Counter
from datetime import datetime
import math

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
        
        # Travel planner - enhanced keywords for comprehensive coverage
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
            keywords['high'].extend(['methodology', 'results', 'conclusion', 'abstract', 'literature', 'analysis', 'experiment', 'data', 'findings', 'discussion'])
            
        # Business/Investment personas
        elif any(word in persona_text for word in ['analyst', 'investment', 'business', 'financial']):
            keywords['high'].extend(['revenue', 'profit', 'financial', 'market', 'growth', 'investment', 'performance', 'strategy', 'competitive', 'analysis'])
            
        # Student personas
        elif any(word in persona_text for word in ['student', 'undergraduate', 'learner']):
            keywords['high'].extend(['introduction', 'basics', 'fundamentals', 'concepts', 'examples', 'practice', 'exercises', 'summary'])
            
        # HR Professional
        elif 'hr' in persona_text or 'human resources' in persona_text:
            keywords['high'].extend(['form', 'onboarding', 'compliance', 'policy', 'procedure', 'document', 'workflow', 'process'])
            
        # Food/Catering
        elif any(word in persona_text for word in ['food', 'contractor', 'chef', 'catering']):
            keywords['high'].extend(['recipe', 'ingredient', 'cooking', 'preparation', 'menu', 'vegetarian', 'buffet', 'serving'])
        
        # Job-specific keywords from task description
        job_words = re.findall(r'\b\w{3,}\b', job_text)
        keywords['medium'].extend([word.lower() for word in job_words if len(word) > 3])
        
        # Add numbers for group planning
        if any(word in job_text for word in ['group', 'friends', 'people']):
            keywords['medium'].extend(['group', 'friends', 'people', 'party', 'together'])
        
        self.importance_keywords = dict(keywords)
    
    def extract_text_with_structure(self, doc):
        """Extract text with structural information"""
        document_content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            page_content = []
            
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    line_text = ""
                    font_sizes = []
                    
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            line_text += text + " "
                            font_sizes.append(span.get("size", 12))
                    
                    if line_text.strip():
                        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                        page_content.append({
                            "text": line_text.strip(),
                            "font_size": avg_font_size,
                            "bbox": block.get("bbox", [0, 0, 0, 0]),
                            "page": page_num + 1
                        })
            
            document_content.append(page_content)
        
        return document_content
    
    def identify_sections(self, document_content, doc_name):
        """Identify sections in the document with improved detection"""
        sections = []
        all_font_sizes = []
        
        # Collect all font sizes to determine heading thresholds
        for page_content in document_content:
            for line in page_content:
                all_font_sizes.append(line["font_size"])
        
        if not all_font_sizes:
            return sections
            
        font_counter = Counter(all_font_sizes)
        body_font = font_counter.most_common(1)[0][0]
        heading_threshold = body_font + 0.5  # Lower threshold for better detection
        
        current_section = None
        section_content = []
        
        for page_content in document_content:
            for line in page_content:
                text = line["text"]
                font_size = line["font_size"]
                page_num = line["page"]
                
                # Enhanced heading detection
                is_heading = (
                    font_size >= heading_threshold or
                    any(re.match(pattern, text) for pattern in self.section_patterns) or
                    (len(text) < 150 and text.strip().endswith(':')) or  # Section headers ending with :
                    (len(text) < 100 and text.isupper() and len(text.split()) <= 10) or
                    (text.strip().startswith(('Chapter', 'Section', 'Part', 'Guide to', 'Introduction to'))) or
                    (re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', text) and len(text.split()) <= 6)  # Title Case headings
                )
                
                # Additional check for travel-specific headings
                travel_headings = [
                    'cities', 'restaurants', 'hotels', 'activities', 'attractions', 'nightlife',
                    'entertainment', 'beaches', 'cuisine', 'food', 'dining', 'accommodation',
                    'transport', 'getting around', 'tips', 'tricks', 'packing', 'budget',
                    'itinerary', 'things to do', 'must see', 'must visit', 'experiences',
                    'adventures', 'coastal', 'culture', 'traditions', 'history'
                ]
                
                if any(keyword in text.lower() for keyword in travel_headings):
                    if len(text) < 200 and len(text) > 10:  # Reasonable heading length
                        is_heading = True
                
                if is_heading and len(text.strip()) > 3:
                    # Save previous section
                    if current_section and section_content:
                        current_section["content"] = " ".join(section_content)
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "document": doc_name,
                        "section_title": text.strip(),
                        "page_number": page_num,
                        "font_size": font_size
                    }
                    section_content = []
                else:
                    # Add to current section content
                    if current_section:
                        section_content.append(text)
                    elif not sections:  # If no section started yet, create a default one
                        current_section = {
                            "document": doc_name,
                            "section_title": f"Introduction - {doc_name.replace('.pdf', '')}",
                            "page_number": page_num,
                            "font_size": font_size
                        }
                        section_content = [text]
        
        # Don't forget the last section
        if current_section and section_content:
            current_section["content"] = " ".join(section_content)
            sections.append(current_section)
        
        return sections
    
    def calculate_importance_score(self, section):
        """Calculate importance score with enhanced logic"""
        title = section.get("section_title", "").lower()
        content = section.get("content", "").lower()
        text = title + " " + content
        
        score = 0
        
        # High importance keywords (3x multiplier)
        for keyword in self.importance_keywords.get('high', []):
            title_matches = title.count(keyword.lower()) * 5  # Extra bonus for title matches
            content_matches = content.count(keyword.lower()) * 3
            score += title_matches + content_matches
        
        # Medium importance keywords (2x multiplier)
        for keyword in self.importance_keywords.get('medium', []):
            score += text.count(keyword.lower()) * 2
        
        # Travel-specific bonuses
        travel_priority_terms = {
            'cities': 8, 'guide': 6, 'comprehensive': 5, 'activities': 7, 'things to do': 8,
            'nightlife': 6, 'entertainment': 6, 'restaurants': 7, 'dining': 6,
            'accommodation': 7, 'hotels': 7, 'tips': 6, 'tricks': 5, 'packing': 5,
            'coastal': 7, 'adventures': 7, 'beaches': 7, 'experiences': 6
        }
        
        for term, bonus in travel_priority_terms.items():
            if term in title:
                score += bonus
            elif term in content[:500]:  # Early content gets bonus
                score += bonus * 0.5
        
        # Content quality bonuses
        content_length = len(content)
        if content_length > 500:
            score += min(content_length / 500, 3)  # Up to 3 bonus points for length
        
        # Early document position bonus (important sections often come first)
        page_bonus = max(0, 4 - (section.get("page_number", 1) * 0.3))
        score += page_bonus
        
        # Diversity bonus - prefer different document types
        doc_name = section.get("document", "").lower()
        if 'cities' in doc_name:
            score += 2
        elif 'things' in doc_name or 'activities' in doc_name:
            score += 2
        elif 'tips' in doc_name or 'tricks' in doc_name:
            score += 1.5
        elif 'nightlife' in doc_name or 'entertainment' in doc_name:
            score += 1.5
        elif 'restaurants' in doc_name or 'hotels' in doc_name:
            score += 1.5
        
        return score
    
    def extract_subsections(self, sections, max_subsections=20):
        """Extract diverse subsections from top sections"""
        subsections = []
        doc_coverage = defaultdict(int)
        max_per_doc = 3  # Limit per document for diversity
        
        for section in sections[:15]:  # Process top 15 sections
            if doc_coverage[section["document"]] >= max_per_doc:
                continue
                
            content = section.get("content", "").strip()
            if not content or len(content) < 100:
                continue
            
            # Split content into meaningful chunks
            # First try to split by bullet points or numbered lists
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
                        
                    if len(current_chunk) + len(sentence) < 350:
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
                    
                if len(chunk) > 50 and len(chunk) < 500:  # Good chunk size
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
        """Process a collection of documents based on input JSON"""
        
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
                document_content = self.extract_text_with_structure(doc)
                sections = self.identify_sections(document_content, filename)
                
                # Calculate importance scores
                for section in sections:
                    section["importance_score"] = self.calculate_importance_score(section)
                
                all_sections.extend(sections)
                doc.close()
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        
        # Sort sections by importance and assign ranks
        all_sections.sort(key=lambda x: x["importance_score"], reverse=True)
        
        # Prepare extracted sections with better diversity
        extracted_sections = []
        seen_titles = set()
        doc_coverage = defaultdict(int)
        max_per_doc = 2  # Limit sections per document for diversity
        
        for i, section in enumerate(all_sections, 1):
            title = section["section_title"].strip()
            doc_name = section["document"]
            
            # Skip if title too similar to existing ones
            title_lower = title.lower()
            is_duplicate = False
            for seen_title in seen_titles:
                if (title_lower in seen_title.lower() or seen_title.lower() in title_lower) and len(title_lower) > 10:
                    is_duplicate = True
                    break
            
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
        
        # Generate diverse subsection analysis
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