# Approach Explanation

## Overview

The `jobTaskMapper` system is designed to intelligently analyze and extract relevant information from collections of PDF documents based on specific user personas and tasks. This is accomplished through a combination of robust PDF parsing, text segmentation using font analysis, and advanced natural language processing (NLP) for semantic content matching.

## Methodology

### 1. PDF Parsing & Section Segmentation

- The system uses **PyMuPDF** to open and parse each PDF file.
- For each page, it analyzes text blocks and uses font size and boldness to identify likely section headings.
- Section titles and their text content are extracted and grouped along with their originating page number and document name.
- A filtering mechanism checks for common verb stems to avoid false titles, improving section accuracy.

### 2. Semantic Analysis & Relevance Ranking

- Each persona and task description is combined into a single query string.
- We use the **sentence-transformers** library with the pre-downloaded `BAAI/bge-base-en-v1.5` model (less than 1GB), ensuring compliance with size and compute constraints.
- The query string and all document sections are encoded into semantic embeddings on CPU.
- We calculate the relevance of each section using cosine similarity between the query and each section's embedding.
- Sections are ranked, and the most relevant (typically top 5) are selected for output.

### 3. Refined Subsection Extraction

- The text of each top-ranked section is further cleaned and reformatted.
- Special handling ensures recipe or instructional sections are concise and easy to follow by reformatting ingredients and instructions.

### 4. Output Formatting

- The results are output in a strict JSON format that includes:
  - **Metadata**: List of input documents, persona, job, and a processing timestamp.
  - **Extracted Sections**: For each, document name, title, page number, and importance rank.
  - **Subsection Analyses**: Document name, page number, and the refined text from that section.

## Resource Efficiency and Constraints

- The system is designed to **run on CPU only**; GPU usage is disallowed using environment variables in the Docker container.
- All models are downloaded and cached at Docker build-time, ensuring **no internet access is required at runtime**.
- With an efficient model and batched encoding, processing time for a collection of 3–5 PDFs remains under 60 seconds.
- The approach is robust to diverse PDF layouts because of the font-based section detection and flexible NLP matching.

## Summary

This end-to-end method ensures the most relevant and actionable content is extracted from diverse PDF sources for a given persona and task, while fully respecting resource, runtime, and security constraints. The modular structure and strict output formatting also allow easy integration into larger automation pipelines.
