

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


### 📊 Challenge 1B – Requirement vs Our Solution

| Aspect                    | Requirement (from Hackathon Doc)                                                                                                           | Our Solution (Team Geni Coders)                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Goal**                  | Extract **most relevant sections** (based on persona + job-to-be-done) from a **collection of PDFs** and return them in a structured JSON. | Analyzes persona & job context → scores document sections → returns top 25 sections + top 20 short refined chunks. |
| **Input**                 | A **JSON input file** with persona, job description, and list of 3–10 PDFs (max 500 pages total).                                          | Accepts `challenge1b_input.json` with PDFs placed in subfolder `/PDFs/`.                                           |
| **Output Format**         | JSON with metadata, selected sections (ranked), and short relevant passages.                                                               | Outputs clean JSON with metadata, top sections, and \~20 refined chunks for quick read.                            |
| **Persona Understanding** | Must personalize output by understanding persona's **role** and **goal/task**.                                                             | Uses keyword-mapping per persona type (student, researcher, HR, etc.) + task-specific keywords.                    |
| **Section Relevance**     | Must prioritize sections relevant to the job using heuristics (no LLMs or heavy models).                                                   | Uses a weighted scoring mechanism: title hits (x5), content hits (x3), position bonus, heading level bonus.        |
| **Execution Time**        | ≤60 seconds per collection (≤10 PDFs, ≤500 pages total).                                                                                   | Achieves fast processing by modularizing per-PDF analysis and optimizing scoring logic.                            |
| **Docker Constraints**    | Must run via Docker, offline, with no internet or external APIs.                                                                           | ✅ Fully dockerized, no network used, no external APIs, works on `linux/amd64`.                                     |
| **Model Use**             | Models allowed only if embedded & within Docker image limit (≤1GB).                                                                        | No external model used. Logic is keyword-driven + rule-based heading parser built on top of 1A.                    |
| **Subsection Extraction** | Should extract **refined snippets** (\~2–4 lines) from selected sections for better readability.                                           | Implements sentence grouping and bullet/number list splitting to produce short, meaningful snippets.               |
| **Output Limit**          | Max 25 sections and 20 refined snippets.                                                                                                   | Honors limits strictly – outputs top 25 scored sections and max 20 refined text chunks across documents.           |

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

