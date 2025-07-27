import os
import json
import time
import fitz  # PyMuPDF
import re
from collections import Counter
from sentence_transformers import SentenceTransformer, util

# Optional: Uncomment if spaCy is available for better verb extraction
# import spacy
# nlp = spacy.load("en_core_web_sm")

# --- Configurable paths (adjust as necessary) ---
INPUT_FILE = "Collection 2/challenge1b_input.json"
OUTPUT_FILE = "Collection 2/challenge1b_output.json"
PDF_DIR = "Collection 2/PDFs"


def get_body_font_size(page):
    """
    Estimate the prevailing body font size by frequency on a page.
    """
    sizes = {}
    try:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    sz = round(span["size"], 2)
                    sizes[sz] = sizes.get(sz, 0) + 1
    except Exception:
        pass
    if not sizes:
        return 10.0
    return max(sizes, key=sizes.get)


def extract_all_texts(docs):
    """
    Extract all text lines from all PDFs to analyze frequent verbs or words.
    Returns list of strings (lines).
    """
    all_text_lines = []
    for doc_meta in docs:
        pdf_path = os.path.join(PDF_DIR, doc_meta["filename"])
        if not os.path.isfile(pdf_path):
            continue
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    blocks = page.get_text("dict")["blocks"]
                    for block in blocks:
                        if block["type"] != 0:
                            continue
                        for line in block["lines"]:
                            line_text = "".join(span["text"] for span in line["spans"]).strip()
                            if line_text:
                                all_text_lines.append(line_text)
        except Exception:
            continue
    return all_text_lines


def extract_verbs_from_texts(texts, top_k=50):
    """
    Extract the most frequent verbs from a list of text strings.
    Returns a set of verbs (lowercased).

    If spaCy is available, use it for POS tagging:
    Uncomment spaCy import and initialization above,
    and uncomment this function's spaCy code.

    If spaCy unavailable, fallbacks to heuristic extraction.
    """

    # If spaCy is available, uncomment this block:
    # verbs = []
    # for text in texts:
    #     doc = nlp(text)
    #     for token in doc:
    #         if token.pos_ == 'VERB':
    #             verbs.append(token.lemma_.lower())
    # most_common_verbs = [v for v, _ in Counter(verbs).most_common(top_k)]
    # return set(most_common_verbs)

    # ===== Heuristic fallback =====
    words = []
    verb_suffixes = ('ed', 'ing', 's', 'es', 'en')
    for text in texts:
        tokens = re.findall(r"\b\w+\b", text.lower())
        for w in tokens:
            if w.endswith(verb_suffixes) or len(w) > 3:
                words.append(w)
    common_words = [w for w, c in Counter(words).most_common(top_k)]

    # Return as a set
    return set(common_words)


def is_likely_title(text, forbidden_starts):
    """
    Check if a line is likely a title header:
    - Not too long (<= 15 words)
    - No trailing punctuation typically seen in instructions
    - Mostly alphabetic words and spaces
    - Starts NOT with a dynamically determined verb from the document
    """
    text = text.strip()
    if not (1 < len(text.split()) <= 15):
        return False
    if text[-1] in ".,":  # trailing punctuation for structural clarity
        return False

    # Reject lines with disallowed punctuation inside (allow alnum, spaces, - and ')
    if re.search(r"[^\w\s\-']", text):
        return False

    first_word = text.lower().split()[0]
    if first_word in forbidden_starts:
        return False

    # Ensure at least one alphabetic character
    return any(c.isalpha() for c in text)


def extract_sections(doc, forbidden_starts, max_sections=1000):
    """
    Extract sections based on font heuristics and dynamic verb filtering for title detection.
    """
    sections = []
    current_title = None
    current_text_lines = []
    current_page = None

    for page_num, page in enumerate(doc, start=1):
        body_size = get_body_font_size(page)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                first_span = line["spans"][0]
                font_size = round(first_span["size"], 2)
                bold = (first_span["flags"] & 16) > 0
                line_text = "".join(s["text"] for s in line["spans"]).strip()
                if not line_text:
                    continue

                is_title_candidate = (
                    (font_size > body_size * 1.15 or (bold and font_size >= body_size))
                    and is_likely_title(line_text, forbidden_starts)
                )

                if is_title_candidate:
                    if current_title and current_text_lines:
                        joined_text = "\n".join(current_text_lines).strip()
                        if len(joined_text) > 50:
                            sections.append({
                                "title": current_title,
                                "text": joined_text,
                                "page_num": current_page,
                            })
                            if len(sections) >= max_sections:
                                return sections

                    current_title = line_text
                    current_text_lines = []
                    current_page = page_num
                else:
                    current_text_lines.append(line_text)

    if current_title and current_text_lines:
        joined_text = "\n".join(current_text_lines).strip()
        if len(joined_text) > 50:
            sections.append({
                "title": current_title,
                "text": joined_text,
                "page_num": current_page,
            })
    return sections


def refine_titles(sections):
    """
    Merge fragmented or incomplete trailing titles into preceding ones.
    """
    refined = []
    buffer_sec = None
    for sec in sections:
        title = sec["title"]
        if title.endswith(('.', ':', ',')) or len(title) <= 3:
            if buffer_sec:
                buffer_sec["title"] += " " + title
                buffer_sec["text"] += "\n" + sec["text"]
            else:
                buffer_sec = sec
        else:
            if buffer_sec:
                refined.append(buffer_sec)
            buffer_sec = sec
    if buffer_sec:
        refined.append(buffer_sec)
    return refined


def clean_section_text(text):
    """
    Format section text into a single paragraph with clear ingredients/instructions,
    separated by period and space, no newlines.
    """
    if not text:
        return ""

    text = re.sub(r"\r\n|\r", "\n", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    ingredients_start = None
    instructions_start = None

    for i, line in enumerate(lines):
        lline = line.lower()
        if "ingredients" in lline:
            ingredients_start = i
        elif any(x in lline for x in ["instructions", "directions", "method"]):
            instructions_start = i

    ingredients_lines = []
    instructions_lines = []

    if ingredients_start is not None and instructions_start is not None:
        if ingredients_start < instructions_start:
            ingredients_lines = lines[ingredients_start + 1 : instructions_start]
            instructions_lines = lines[instructions_start + 1 :]
        else:
            instructions_lines = lines[instructions_start + 1 : ingredients_start]
            ingredients_lines = lines[ingredients_start + 1 :]
    elif ingredients_start is not None:
        ingredients_lines = lines[ingredients_start + 1 :]
    elif instructions_start is not None:
        instructions_lines = lines[instructions_start + 1 :]
    else:
        return _reformat_general_text_singleline(lines)

    ingredients_text = _reformat_ingredients_singleline(ingredients_lines)
    instructions_text = _reformat_instructions_singleline(instructions_lines)

    parts = []
    if ingredients_start is not None:
        parts.append("Ingredients: " + ingredients_text)
    if instructions_start is not None or instructions_text.strip():
        parts.append("Instructions: " + instructions_text)

    return ". ".join(parts).strip() + "."


def _reformat_ingredients_singleline(lines):
    bullet_re = re.compile(r"^[-•*o]\s*")
    items = []
    for line in lines:
        line = bullet_re.sub("", line).strip()
        if line:
            items.append(line)
    return ", ".join(items)


def _reformat_instructions_singleline(lines):
    if not lines:
        return ""
    numbered_re = re.compile(r"^\d+[\.\)]\s*")
    bullet_re = re.compile(r"^[-•*o]\s*")

    is_numbered = any(numbered_re.match(line) for line in lines)
    is_bulleted = any(bullet_re.match(line) for line in lines)

    if is_numbered or is_bulleted:
        steps = []
        for line in lines:
            step = numbered_re.sub("", line)
            step = bullet_re.sub("", step)
            step = step.strip()
            if step:
                steps.append(step)
        return " ".join(steps)
    else:
        return " ".join(lines).strip()


def _reformat_general_text_singleline(lines):
    bullet_re = re.compile(r"^[-•*o]\s*")
    cleaned = []
    for line in lines:
        if bullet_re.match(line):
            line = bullet_re.sub("", line)
        if line.strip():
            cleaned.append(line.strip())
    return " ".join(cleaned)


def main():
    start_time = time.time()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        inp = json.load(f)

    persona = inp.get("persona", {}).get("role", "Unknown Persona")
    job = inp.get("job_to_be_done", {}).get("task", "No task specified")
    documents = inp.get("documents", [])

    model_name = os.getenv("MODEL_NAME", "BAAI/bge-base-en-v1.5")
    print(f"Loading embedding model {model_name} ...")
    model = SentenceTransformer(model_name)

    max_docs = int(os.getenv("MAX_DOCS_TO_PROCESS", str(len(documents))))
    max_sections = int(os.getenv("MAX_SECTIONS_TO_PROCESS", "1000"))
    max_output = int(os.getenv("MAX_OUTPUT_SECTIONS", "5"))

    docs_to_process = documents[:max_docs]

    # Extract all texts to build dynamic verbs list
    all_text_lines = extract_all_texts(docs_to_process)
    forbidden_starts = extract_verbs_from_texts(all_text_lines)

    all_sections = []

    # Extract sections using dynamic verb filtering
    for doc_meta in docs_to_process:
        pdf_path = os.path.join(PDF_DIR, doc_meta["filename"])
        if not os.path.isfile(pdf_path):
            print(f"Warning: PDF {pdf_path} not found, skipping.")
            continue
        try:
            with fitz.open(pdf_path) as doc:
                secs = extract_sections(doc, forbidden_starts, max_sections=max_sections)
                for s in secs:
                    s["document"] = doc_meta["filename"]
                all_sections.extend(secs)
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            continue

    if not all_sections:
        print("No sections extracted from documents.")
        output = {
            "metadata": {
                "input_documents": [d["filename"] for d in docs_to_process],
                "persona": persona,
                "job_to_be_done": job,
                "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "extracted_sections": [],
            "subsection_analysis": []
        }
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
            json.dump(output, f_out, indent=4, ensure_ascii=False)
        return

    # Refine fragmented titles
    all_sections = refine_titles(all_sections)

    # Compose embedding query
    query_text = f"Persona: {persona}. Job to be done: {job}."
    query_emb = model.encode(query_text, normalize_embeddings=True)

    contexts = [f"{sec['title']}: {sec['text']}" for sec in all_sections]
    embeddings = model.encode(contexts, normalize_embeddings=True, batch_size=32)

    for i, sec in enumerate(all_sections):
        sec['relevance'] = util.cos_sim(query_emb, embeddings[i]).item()

    ranked_sections = sorted(all_sections, key=lambda x: x['relevance'], reverse=True)

    seen = set()
    extracted_sections = []
    subsection_analysis = []
    rank = 1
    for sec in ranked_sections:
        if sec['title'] in seen:
            continue
        seen.add(sec['title'])

        extracted_sections.append({
            "document": sec["document"],
            "section_title": sec["title"],
            "importance_rank": rank,
            "page_number": sec["page_num"]
        })

        refined_text = clean_section_text(sec["text"])
        subsection_analysis.append({
            "document": sec["document"],
            "refined_text": refined_text,
            "page_number": sec["page_num"]
        })

        rank += 1
        if rank > max_output:
            break

    output_json = {
        "metadata": {
            "input_documents": [d["filename"] for d in docs_to_process],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        json.dump(output_json, f_out, indent=4, ensure_ascii=False)

    elapsed = time.time() - start_time
    print(f"Processing completed in {elapsed:.2f} seconds. Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
