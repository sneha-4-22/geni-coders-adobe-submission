

---

## 📘 README.md — Challenge 1B: Persona-Driven Section Extraction

---

### 🚀 Objective

This solution performs **intelligent, persona-driven extraction** of the most **relevant sections** from multiple PDFs. It is tailored to help different users (e.g., students, researchers, travel planners) **quickly access key content** aligned with their interests and tasks.

---

### 🔁 Builds Upon Challenge 1A

This solution **reuses and extends the modular extraction logic** implemented in [Challenge 1A](../challenge_1a/README.md), including:

* **Title extraction** from the first page
* **Hierarchical heading detection** (`H1`, `H2`, `H3`)
* **Font-size–based structural parsing**

These components ensure consistent heading hierarchy across the corpus before applying persona-based filtering.

---

### 🧠 Methodology (Layman’s Terms)

1. 📄 For every PDF in the input folder:

   * Extract the **main sections and their content**.
   * Identify headings based on **font size**, **text layout**, and **page structure**.

2. 👤 Use the provided **persona and job-to-be-done**:

   * Analyze keywords that the persona would find **important**.
   * Assign **importance scores** to each section based on keyword frequency, content length, and position in document.

3. 🏆 Return the **top 25 most important sections** across all documents.

4. 📌 Also extract short **subsections** from top-scoring content for better coverage.

---

### 🧪 Methodology (Technical Highlights)

* **Heading Detection:** Uses Challenge 1A font-mapping, span density, and average span width.
* **Scoring:** Importance = weighted keyword frequency + content length bonus + document position + heading level.
* **Subsection Extraction:** Content split based on bullets, numbered lists, or grouped sentence blocks.
* **Diversity Guarantee:** Limits section count per document and avoids duplicates.

---



### 🔧 How to Run (Docker)

1. Navigate to this folder:

```bash
cd challenge_1b
```

2. Build the Docker image:

```bash
 docker build --platform linux/amd64 -t challenge1b:latest . 
```

3. Run the container with input/output mounts:

```bash
 docker run --rm -v ${pwd}:/app/input -v ${pwd}/output:/app/output --network none challenge1b:latest
```

---

### 📥 Input Format

Each collection folder inside `input/` must contain a file called `challenge1b_input.json`:

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

Ensure the referenced PDFs are present in:
`input/<collection_name>/PDFs/`

---

### 📤 Output Format

Each result file in `output/` contains:

* Metadata (persona, task, timestamp)
* `extracted_sections` (Top 25 ranked sections)
* `subsection_analysis` (Short and useful content blocks)

---
