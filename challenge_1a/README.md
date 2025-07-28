

---

#  Challenge 1A – Document Outline Extraction

**Round 1A Solution – Adobe Hackathon by Team Geni Coders**

##  Problem Statement

We are given a PDF file and asked to extract its **title** and hierarchical **outline** (H1, H2, H3 headers), along with their respective **page numbers**, in a clean JSON format.

---

## Approach


Imagine you are reading a PDF and trying to create a Table of Contents.
You look for the **biggest title** on the first page — that’s probably the name of the document. Then you scan through each page and spot the **larger or bolder lines** that look like chapter headings (like "1 Introduction", "2.1 Background", etc.).

That’s exactly what we made the program do — it:

* **Finds the main title** on the first page.
* **Goes through each page**, one by one.
* Looks for **text that is bigger or more prominent** than normal text.
* Checks if it follows heading-like patterns (e.g., `1`, `1.1`, `1.1.1`, or ends with `:`).
* **Maps those lines** into H1, H2, or H3 headings and adds their page numbers.

---

###  Technical Methodology

#### 1. **PDF Parsing with PyMuPDF (fitz)**

We load the document using the `fitz` library and extract text spans from each page.

#### 2. **Title Detection**

* We analyze the **first page only**.
* We select spans that are **not footers/headers**, not URLs, not all-uppercase junk, etc.
* From the valid candidates, we take the **text with the largest font size** as the title.

#### 3. **Heading Detection**

* For every page:

  * We extract **text spans** and filter out headers/footers.
  * We collect **font sizes** to determine the common body text size.
  * Then we check for potential headings based on:

    * **Font size** (bigger than body size).
    * **Span structure** (short phrases, wider spans).
    * **Pattern matching** (e.g., numbers like `1.2`, or lines ending with `:`).
* We then assign headings as:

  * `H1` if pattern is like `1`, or highest font size group.
  * `H2` for `1.2` or next font size.
  * `H3` for `1.2.3` or smaller yet noticeable fonts.

#### 4. **Hierarchical Mapping**

Earlier, heading extraction was attempted across the entire document at once. But for better **accuracy and hierarchy preservation**, we now extract and analyze **spans per page**.
This allows us to:

* Better differentiate local headings.
* Avoid mixing up body content across pages.
* Retain clean and proper heading structures.

#### 5. **JSON Output**

Each PDF produces an output in the following structure:

```json
{
  "title": "Sample Title",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Background", "page": 2 },
    ...
  ]
}
```

---

##  Why This Works Well

* **Flexible**: Doesn’t rely purely on font sizes — also uses patterns, punctuation, and structure.
* **Fast**: Handles multiple PDFs within the 10-second constraint.
* **Robust**: Skips headers, footers, junk characters, URLs, etc.
* **Modular**: Each function does a focused job (title detection, span filtering, etc.) which makes it easier to improve or reuse later.




---

### 📊 Challenge 1A – Requirement vs Our Solution

| Aspect                 | Requirement (from Hackathon Doc)                                                                     | Our Solution (Team Geni Coders)                                                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Goal**               | Extract document **title** and **outline** (headings H1–H3) with **page numbers**, in a JSON format. | Extracts title using smart heuristics on Page 1 and detects H1–H3 headings across pages with page number tagging. |
| **Input**              | A **single PDF file** (≤50 pages).                                                                   | Takes one PDF per run via Docker-mounted `input/`, processes all pages.                                           |
| **Output Format**      | JSON file containing title and outline with heading levels and page numbers.                         | Outputs clean structured JSON like: `{ "title": ..., "outline": [ {level, text, page} ] }`                        |
| **Heading Levels**     | Must support hierarchical headings (e.g., H1, H2, H3).                                               | Implements rule-based heading level detection using font size + patterns like `1.2`, `1.2.3`, etc.                |
| **Execution Time**     | ≤10 seconds (on 50-page document, AMD64 CPU only).                                                   | Optimized for speed; completes <10 seconds per PDF during testing.                                                |
| **Docker Constraints** | Must run via Docker, offline, with no internet access.                                               | ✅ Fully dockerized, CPU-only, works offline without external dependencies.                                        |
| **Model Use**          | Allowed, but model size + Docker image must stay within 200MB.                                       | Doesn’t use any ML model – purely rule-based, lightweight logic.                                                  |


---

##  How to Run the Code

1. Open terminal and navigate to the challenge folder:

```bash
cd challenge_1a
```

2. Build the Docker image:

```bash
docker build -t pdf-extractor:latest .
```

3. Run the container with input/output bindings:

```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none pdf-extractor:latest
```

* Place PDFs in `input/` folder.
* JSON outputs will be available in `output/`.

---


