

# Challenge 1B – Persona-Driven Section Extraction

**Round 1B Solution – Adobe Hackathon by Team Geni Coders**

---

## Problem Statement

Given a persona and a job-to-be-done, the task is to analyze a collection of PDF documents and extract the most relevant sections personalized to that user. The system should return top sections and subsections that help the user achieve their goal quickly.

---

## Builds Upon Challenge 1A

This solution reuses and extends modular logic built in [Challenge 1A](../challenge_1a/README.md), including:

* Title extraction from the first page
* Heading detection (H1, H2, H3) using font size and text layout
* Structured span filtering and heading-level mapping

---

## Approach 

1. For each PDF:

   * Extract title and section-wise content using headings.
   * Group content under those headings.

2. Analyze the persona (e.g., student, researcher) and their job-to-be-done (e.g., "learn basics of networking").

3. Use keywords from the persona and task to score each section.

4. Rank and select top 25 relevant sections across all documents.

5. From these, extract smaller paragraph-sized chunks (subsections) to improve coverage and readability.

---

## Technical Methodology

### 1. Persona Keyword Setup

* Uses pre-defined keyword lists for personas like:

  * Students
  * Researchers
  * Travel planners
  * HR professionals
* Also extracts additional keywords from the task description.

### 2. Section Extraction

* Uses Challenge 1A logic to:

  * Filter spans
  * Detect headings via font size, layout, and patterns (e.g., numbered headings, colons)
  * Group text into sections

### 3. Importance Scoring

Each section is scored using:

* High importance keyword in title: +5
* High keyword in content: +3
* Medium keywords: +2
* Long content (>300 chars): +1 to +3
* Earlier page bonus: up to +3
* Heading level bonus: H1 > H2 > H3

### 4. Top Section Selection

* Selects top 25 sections by score
* Max 3 sections per document
* Avoids near-duplicate titles

### 5. Subsection Extraction

* Extracts 1-2 sentence chunks or bullets from top 15 sections
* Limits to 20 diverse subsections from across documents

---

## Input Format

Each input collection goes inside `input/` and should include:

### challenge1b\_input.json

```json
{
  "persona": {
    "role": "Undergraduate Student"
  },
  "job_to_be_done": {
    "task": "Understand basics of computer networks"
  },
  "documents": [
    { "filename": "networks101.pdf" },
    { "filename": "osi_layers.pdf" }
  ]
}
```

### PDF files

Must be located inside:
`input/<collection_name>/PDFs/`

---

## Output Format

Saved to `output/` as `<collection_name>_output.json`:

```json
{
  "metadata": {
    "input_documents": [...],
    "persona": "...",
    "job_to_be_done": "...",
    "processing_timestamp": "..."
  },
  "extracted_sections": [
    {
      "document": "osi_layers.pdf",
      "section_title": "Routing Basics",
      "importance_rank": 1,
      "page_number": 3
    }
  ],
  "subsection_analysis": [
    {
      "document": "networks101.pdf",
      "refined_text": "The OSI model is a conceptual framework...",
      "page_number": 2
    }
  ]
}
```

---

## How to Run (Docker)

1. Go to the challenge folder:

```bash
cd challenge_1b
```

2. Build the Docker image:

```bash
docker build --platform linux/amd64 -t challenge1b:latest .
```

3. Run the container:

```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none challenge1b:latest
```

---

## Why It Works

* Personalized output using domain-specific keywords
* Structured content extraction reusing proven logic from 1A
* Fast, dockerized pipeline
* JSON-based output for easy downstream integration

---

## Team

Built by **Team Geni Coders**
for **Adobe India Hackathon 2025 – Round 1B**

