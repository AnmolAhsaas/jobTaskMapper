# jobTaskMapper

## Overview
An intelligent PDF analysis and content extraction system that processes multiple document collections to extract relevant content based on specific personas and use cases. The system uses semantic analysis and natural language processing to identify and rank important sections from PDF documents.

## Features
- **Multi-Collection Processing**: Handles multiple document collections simultaneously
- **Persona-Based Analysis**: Extracts content relevant to specific user personas and tasks
- **Semantic Text Analysis**: Uses sentence transformers for intelligent content matching
- **Importance Ranking**: Ranks extracted sections by relevance to the given task
- **JSON-Based Configuration**: Flexible input/output format for easy integration

## Project Structure
```
jobTaskMapper/
├── Collection 1/                    # Travel Planning Documents
│   ├── PDFs/                       # South of France travel guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 2/                    # Adobe Acrobat Learning
│   ├── PDFs/                       # Acrobat tutorial documents
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 3/                    # Recipe Collection
│   ├── PDFs/                       # Cooking and recipe guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── run.py                          # Main application script
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Docker (optional, for containerized execution)

### Local Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd jobTaskMapper
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your PDF files are placed in the appropriate collection directories under `PDFs/` folders.

### Docker Installation (Recommended)
For a consistent environment across different systems, you can use Docker:

1. Build the Docker image:
   ```bash
   docker build --platform linux/amd64 -t pdf-runner .
   ```

2. Run the application in a Docker container:
   ```bash
   docker run --rm -v "${PWD}:/app" -w /app pdf-runner
   ```

   This command:
   - `--rm`: Automatically removes the container when it exits
   - `-v "${PWD}:/app"`: Mounts the current directory to `/app` in the container
   - `-w /app`: Sets the working directory inside the container
   - `pdf-runner`: Uses the built Docker image

### Dependencies
- **PyMuPDF**: PDF processing and text extraction
- **sentence-transformers**: Semantic text analysis and embeddings
- **transformers**: Natural language processing models
- **torch**: Deep learning framework
- **numpy**: Numerical computing
- **tqdm**: Progress bars
- **scikit-learn**: Machine learning utilities

## Usage

### Running the Analysis

#### Local Execution
```bash
python run.py
```

#### Docker Execution
```bash
docker run --rm -v "${PWD}:/app" -w /app pdf-runner
```

The script will:
1. Process all collections in the workspace
2. Extract text and identify important sections from PDFs
3. Rank content based on persona and task relevance
4. Generate JSON output files with analysis results

### Configuration
Each collection requires:
- `challenge1b_input.json`: Configuration file with persona and task definition
- `PDFs/` directory: Contains the PDF documents to analyze

## Collections

### Collection 1: Travel Planning
- **Challenge ID**: round_1b_002
- **Persona**: Travel Planner
- **Task**: Plan a 4-day trip for 10 college friends to South of France
- **Documents**: 7 travel guides

### Collection 2: Adobe Acrobat Learning
- **Challenge ID**: round_1b_003
- **Persona**: HR Professional
- **Task**: Create and manage fillable forms for onboarding and compliance
- **Documents**: 15 Acrobat guides

### Collection 3: Recipe Collection
- **Challenge ID**: round_1b_001
- **Persona**: Food Contractor
- **Task**: Prepare vegetarian buffet-style dinner menu for corporate gathering
- **Documents**: 9 cooking guides

## Input/Output Format

### Input JSON Structure
```json
{
  "challenge_info": {
    "challenge_id": "round_1b_XXX",
    "test_case_name": "specific_test_case"
  },
  "documents": [{"filename": "doc.pdf", "title": "Title"}],
  "persona": {"role": "User Persona"},
  "job_to_be_done": {"task": "Use case description"}
}
```

### Output JSON Structure
```json
{
  "metadata": {
    "input_documents": ["list"],
    "persona": "User Persona",
    "job_to_be_done": "Task description"
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Title",
      "importance_rank": 1,
      "page_number": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "refined_text": "Content",
      "page_number": 1
    }
  ]
}
## Output Format

The system generates detailed JSON output files with the following structure:

### Output JSON Structure
```json
{
  "metadata": {
    "input_documents": ["list of processed files"],
    "persona": "User persona description",
    "job_to_be_done": "Task description",
    "processing_timestamp": "timestamp",
    "total_sections_found": "number"
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Section Title",
      "importance_rank": 1,
      "page_number": 1,
      "relevance_score": 0.95
    }
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "refined_text": "Relevant content text",
      "page_number": 1,
      "confidence_score": 0.87
    }
  ]
}
```

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Support
For questions or issues, please create an issue in the repository or contact the development team.

---

**Note**: This system is designed for automated document analysis and content extraction based on specific use cases and personas. Results may vary depending on document quality and complexity.
