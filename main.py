# main.py

import os
from run import main
from sentence_transformers import SentenceTransformer

# Load model once globally
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

for folder in os.listdir("."):
    if not os.path.isdir(folder):
        continue
    if not folder.startswith("Collection "):
        continue

    input_file = os.path.join(folder, "challenge1b_input.json")
    output_file = os.path.join(folder, "challenge1b_output.json")
    pdf_dir = os.path.join(folder, "PDFs")

    if not os.path.isfile(input_file):
        continue

    os.environ["INPUT_FILE"] = input_file
    os.environ["OUTPUT_FILE"] = output_file
    os.environ["PDF_DIR"] = pdf_dir

    print(f"\n📂 Processing: {folder}")
    main(model=model)
