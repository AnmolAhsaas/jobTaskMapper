# PDF Document Structure Extractor – Docker Guide

This guide explains how to build and run the `pdf-runner` project using Docker, and how to organize input/output files for processing multiple document collections.

## Building the Docker Image

To build the Docker image, run:

```bash
docker build --platform linux/amd64 -t pdf-runner .
```

## Directory Structure Requirements

Your project directory structure should be organized as follows:

```
project-root/
├── Collection 1/
│   ├── challenge1b_input.json
│   └── PDFs/
│       ├── file1.pdf
│       ├── file2.pdf
│       └── ...
├── Collection 2/
│   ├── challenge1b_input.json
│   └── PDFs/
│       ├── file1.pdf
│       ├── file2.pdf
│       └── ...
├── Collection 3/
│   ├── challenge1b_input.json
│   └── PDFs/
│       └── ...
└── ...
```

## Important Requirements

Each collection folder **must**:
- Start with the name "Collection" followed by a number (e.g., "Collection 1", "Collection 2")
- Contain a `challenge1b_input.json` file that defines:
  - Persona
  - Task description
  - List of PDF filenames to process
- Include a `PDFs/` folder containing all the referenced PDF files

## Sample Files

Sample files have already been provided to demonstrate the correct structure and format.

## Running the Processor

To run the PDF processor:

```bash
docker run --rm -v "$PWD:/app" -w /app pdf-runner
```

This command:
- Mounts your current folder into the container at `/app`
- Runs the analysis on all Collection folders
- Writes `challenge1b_output.json` next to `challenge1b_input.json` in each Collection folder

## Requirements

- **Internet connection**: NOT required
- **Dependencies**: All models and dependencies are pre-installed in the Docker image

## Summary

1. Organize your folders following the structure above (Collection folders with PDFs subfolder)
2. Build the Docker image
3. Run the container with volume mounting
4. Retrieve outputs from each Collection folder (`challenge1b_output.json`)

The processor will automatically detect and process all folders that start with "Collection" and contain the required structure.