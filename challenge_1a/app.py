import fitz
import os
import json
import time
import string
import re
from collections import Counter

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

def process_pdf_folder(input_dir, output_dir):
    start_time = time.time()
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue

        full_path = os.path.join(input_dir, filename)
        doc = fitz.open(full_path)

        title = extract_title_from_first_page(doc)
        outline = extract_outline_from_doc(doc)

        result = {
            "title": title,
            "outline": outline
        }

        output_file_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"✅ Done in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    input_path = "/app/input"
    output_path = "/app/output"
    os.makedirs(output_path, exist_ok=True)
    process_pdf_folder(input_path, output_path)
