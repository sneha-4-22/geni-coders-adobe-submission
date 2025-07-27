

# Adobe India Hackathon – Round 2 Solution by Geni Coders 👩🏻‍💻

Welcome to our Round 2 submission for the **Adobe India Hackathon - "Connecting the Dots" Challenge**!
This repository showcases our full pipeline across both Round 1A and 1B, focusing on building intelligent, structured, and user-focused PDF experiences.

---

## 🗂 Repository Structure

```
.
├── challenge_1a/               # Round 1A: Outline Extraction from PDFs
│   ├── input/                 # Contains input PDFs
│   ├── output/                # Extracted structured JSONs (title + H1-H3 hierarchy)
│   ├── Dockerfile             # Containerized solution
│   ├── main.py                # Core script for outline extraction
│   └── Readme.md              # Detailed explanation of approach for 1A

├── challenge_1b/               # Round 1B: Persona-Based Document Intelligence
│   ├── Collection 1/
│   │   ├── PDFs/             # Source documents for test case 1
│   │   ├── challenge1b_input.json
│   │   └── challenge1b_output.json
│   ├── Collection 2/         # Folder for additional test cases
│   ├── Collection 3/
│   ├── output/               # Output JSONs per persona-job requirement
│   ├── Dockerfile            # Containerized solution
│   ├── main.py               # Core logic for relevance extraction and ranking
│   └── README.md             # Detailed approach for 1B

```

---

## 🧠 What’s Inside?

* `challenge_1a`: Automatically extracts **Title, H1, H2, H3** sections from PDFs with high accuracy and formats them into JSON outlines.
* `challenge_1b`: Takes in a persona and job-to-be-done along with a document set, and intelligently selects, ranks, and analyzes the most relevant sections per requirement.

Both components are Dockerized and optimized for **offline**, **CPU-only** environments, adhering strictly to Adobe’s runtime and performance constraints.

---

## 🔗 More Details

* To learn more about the **approach and techniques** used, check out the individual READMEs:

  * 📄 [`challenge_1a/Readme.md`](./challenge_1a/Readme.md)
  * 📄 [`challenge_1b/README.md`](./challenge_1b/README.md)


