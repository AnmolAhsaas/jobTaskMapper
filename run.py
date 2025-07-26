import os
import json
import time
import fitz  # PyMuPDF
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Paths (adjust as needed)
INPUT_FILE = "Collection 3/challenge1b_input.json"
OUTPUT_FILE = "Collection 3/challenge1b_output.json"
PDF_DIR = "Collection 3/PDFs"

# Load input JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    inp = json.load(f)

persona = inp["persona"]["role"]
job = inp["job_to_be_done"]["task"]
pdfs = inp["documents"]

print("Loading embedding model...")
embedding_model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")  # Alternative/model recommended

def extract_sections(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        page_title = None
        page_text_lines = []
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                line_texts = [span["text"].strip() for span in line["spans"] if span["text"].strip()]
                for span in line["spans"]:
                    size = span["size"]
                    text = span["text"].strip()
                    if text and size > 11 and not text.startswith("•") and len(text) < 120:
                        page_title = text
                        break
                page_text_lines.extend(line_texts)
                if page_title:
                    break
            if page_title:
                break
        if not page_title and page_text_lines:
            page_title = page_text_lines[0]
        section_text = "\n".join(page_text_lines)
        if page_title:
            sections.append({
                "title": page_title,
                "text": section_text,
                "page_num": page_num + 1
            })
    doc.close()
    filtered = [s for s in sections if s["title"] and s["title"].strip() not in ["•", "", "-", None]]
    return filtered

def rank_sections_by_similarity(sections, query):
    if not sections:
        return []
    query_emb = embedding_model.encode([query])[0]
    sec_texts = [s["text"] for s in sections]
    sec_embs = embedding_model.encode(sec_texts)
    sims = cosine_similarity([query_emb], sec_embs)[0]
    for idx, s in enumerate(sections):
        s["sim"] = sims[idx]
    return sorted(sections, key=lambda x: x["sim"], reverse=True)

def refine_text_extractive(text, query, top_n=3):
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    sentences = [s.strip() for s in text.replace('\n', '. ').split('. ') if s.strip()]
    if not sentences:
        return text
    sent_embs = embedding_model.encode(sentences)
    query_emb = embedding_model.encode([query])
    sims = cos_sim(query_emb, sent_embs)[0]
    top_idx = np.argsort(sims)[-top_n:][::-1]
    return '. '.join([sentences[i] for i in top_idx]) + '.'

def clean_text(text):
    cleaned = text.replace("•", "-").replace("\n", " ").strip()
    cleaned = ' '.join(cleaned.split())
    return cleaned

# Main
all_sections = []
print("Extracting sections from PDFs...")
for doc in tqdm(pdfs, desc="Parsing PDFs"):
    pdf_path = os.path.join(PDF_DIR, doc["filename"])
    secs = extract_sections(pdf_path)
    for s in secs:
        s["document"] = doc["filename"]
        s["document_title"] = doc["title"]
    all_sections.extend(secs)

query_text = f"{persona} {job}"
print("Ranking sections by semantic similarity...")
ranked_sections = rank_sections_by_similarity(all_sections, query_text)

# Select top 5 unique sections (max 1 per document)
final_sections = []
used_docs = set()
for s in ranked_sections:
    if s["document"] not in used_docs:
        final_sections.append({
            "document": s["document"],
            "section_title": s["title"],
            "importance_rank": len(final_sections) + 1,
            "page_number": s["page_num"]
        })
        used_docs.add(s["document"])
    if len(final_sections) >= 5:
        break

print("Extracting summaries for final sections...")
subsection_analysis = []
for sec in tqdm(final_sections, desc="Extracting summaries"):
    sec_obj = next(s for s in all_sections
                   if s["document"] == sec["document"]
                   and s["title"] == sec["section_title"]
                   and s["page_num"] == sec["page_number"])
    refined = refine_text_extractive(sec_obj["text"], query_text, top_n=4)
    cleaned = clean_text(refined)
    subsection_analysis.append({
        "document": sec["document"],
        "refined_text": cleaned,
        "page_number": sec["page_number"]
    })

output_json = {
    "metadata": {
        "input_documents": [d["filename"] for d in pdfs],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    },
    "extracted_sections": final_sections,
    "subsection_analysis": subsection_analysis
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
    json.dump(output_json, f_out, indent=4, ensure_ascii=False)

print(f"Processing completed. Output saved to {OUTPUT_FILE}")
