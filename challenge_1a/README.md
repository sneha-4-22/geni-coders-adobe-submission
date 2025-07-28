

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

<img width="717" height="549" alt="image" src="https://github.com/user-attachments/assets/cabdd8c7-b0ec-47fd-a5f4-5c0ab3a4a64a" />


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

### ✅ Final Validation Checklist 

| Validation Item                                             | ✔ Status | Notes                                                                                              |
| ----------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| **📄 Title Detection from Page 1**                          | ✅ Yes    | `extract_title_from_first_page()` uses font size and filtering to detect a valid title from Page 1 |
| **📑 Heading Extraction (H1, H2, H3)**                      | ✅ Yes    | Implemented via font size analysis and pattern detection (`1.`, `1.1`, `1.1.1`, etc.)              |
| **🧠 Heuristic + Rule-Based Parsing**                       | ✅ Yes    | Rule-based logic only (no ML), ensures lightweight and interpretable logic                         |
| **⚡ Execution Time ≤ 10 seconds for 50-page PDF**           | ✅ Yes    | Optimized with PyMuPDF for fast execution; processed under 10s in all internal tests               |
| **📦 Dockerized with No Internet Use**                      | ✅ Yes    | Docker image uses no internet and fully self-contained offline environment                         |
| **📁 Reads from `/app/input`**                              | ✅ Yes    | All PDFs are automatically loaded from the read-only `/app/input` mount                            |
| **🧾 Writes to `/app/output`**                              | ✅ Yes    | Clean JSON files created and saved to `/app/output`                                                |
| **🔒 Input is Read-Only Mounted**                           | ✅ Yes    | As per Docker spec: `-v $(pwd)/input:/app/input:ro` ensures read-only input                        |
| **🧮 Output Format Matches Schema**                         | ✅ Yes    | Output JSON matches Adobe's required format: `{"title": ..., "outline": [{level, text, page}]}`    |
| **📏 Maximum PDF Length Tested (50 pages)**                 | ✅ Yes    | Successfully tested on large PDFs (50+ pages) without crashing or exceeding time                   |
| **📐 Supports Nested Headings (Hierarchical H1–H3)**        | ✅ Yes    | Levels detected using font size map + pattern classification logic                                 |
| **🧪 Schema Conformance Validated**                         | ✅ Yes    | Output is validated against `output_schema.json` under `sample_dataset/schema/`                    |
| **🧠 No External Models >200MB**                            | ✅ Yes    | No ML models used at all; model size = 0MB                                                         |
| **🧩 Works on AMD64 CPU (not ARM-only)**                    | ✅ Yes    | Dockerfile built using `--platform linux/amd64` — full compatibility ensured                       |
| **🧪 Complex PDFs with Multi-Column/Images Supported**      | ✅ Yes    | Robust against different layouts including images, footers, multi-column pages                     |
| **💾 Memory Usage ≤ 16GB**                                  | ✅ Yes    | Lightweight memory usage; tested within 16GB RAM even on long documents                            |
| **🔁 All PDFs in input folder are processed automatically** | ✅ Yes    | Complete folder-based batch processing built in using `os.listdir(input_dir)` loop                 |




---

##  Why This Works Well

* **Flexible**: Doesn’t rely purely on font sizes — also uses patterns, punctuation, and structure.
* **Fast**: Handles multiple PDFs within the 10-second constraint.
* **Robust**: Skips headers, footers, junk characters, URLs, etc.
* **Modular**: Each function does a focused job (title detection, span filtering, etc.) which makes it easier to improve or reuse later.

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

## 📚 Libraries Used

| Library               | Purpose                                                                                             |
|----------------------|-----------------------------------------------------------------------------------------------------|
| `PyMuPDF (fitz)`      | For efficient PDF parsing, extracting structured text spans and layout info **on a per-page basis**. Used to detect headings (H1, H2, H3) individually on each page to preserve hierarchy accurately. |
| `os`                  | To interact with filesystem directories for reading inputs and writing outputs                      |
| `json`                | For creating structured JSON outputs conforming to required schema                                  |
| `re`                  | For regular expression-based heading pattern detection (e.g., `1.`, `1.1`)                          |
| `string`              | To clean and filter non-alphanumeric characters in title/heading spans                              |
| `time`                | For timing execution and performance tracking                                                       |
| `collections.Counter` | To identify the most common body font size across PDF pages to differentiate headings from body text |

---


