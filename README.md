# PDF Redaction Tool

A Python script that securely redacts specified text from PDF files and optimizes file size using PyMuPDF and qpdf.

## Features

✅ **True Redaction**: Permanently removes text from PDF content (not just visual covering)  
✅ **File Size Optimization**: Reduces PDF size through compression  
✅ **Flexible Text Search**: Redact any text you specify  
✅ **Detailed Reporting**: Shows exactly what was found and redacted  
✅ **Batch Processing**: Works on any PDF file

## How It Works

1. **Search**: Finds all instances of specified text across all pages
2. **Mark**: Creates redaction annotations over found text
3. **Redact**: Permanently removes text from the specified rectangular areas
4. **Optimize**: Compresses the PDF using qpdf for minimal file size

## Requirements

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [qpdf](https://qpdf.readthedocs.io/) (PDF optimization tool)

## Installation

1. **Install qpdf** (if not already installed):
   ```bash
   # macOS
   brew install qpdf
   
   # Ubuntu/Debian
   sudo apt-get install qpdf
   
   # Windows (with Chocolatey)
   choco install qpdf
   ```

2. **Install Python dependencies**:
   ```bash
   uv add pymupdf
   ```

## Usage

```bash
uv run python main.py <pdf_filename> "<text_to_redact>"
```

### Examples

```bash
# Redact license text
uv run python main.py document.pdf "Licensed to John Doe <john@example.com>"

# Redact confidential information
uv run python main.py report.pdf "CONFIDENTIAL"

# Redact personal names
uv run python main.py book.pdf "Jane Smith"
```

### Sample Output

```
Processing: document.pdf
Text to redact: 'Licensed to John Doe <john@example.com>'
Output will be: document_redacted.pdf
Step 1: Performing redaction...
  Found on page 2: 1 instance(s)
  Found on page 3: 1 instance(s)
  Found on page 4: 1 instance(s)
Total instances found and redacted: 3
Step 2: Optimizing with qpdf...
Redaction completed: document_redacted.pdf
Original size: 3.2 MB
Final size: 2.7 MB
Size change: -15.6%
```

## Output

- **Input**: `filename.pdf`
- **Output**: `filename_redacted.pdf`
- The original file is never modified

## Security

This tool performs **true redaction**:
- Text is permanently removed from PDF content
- Cannot be recovered by copy/paste, search, or PDF analysis tools
- Text areas become empty/transparent (showing page background)
- No traces of original text remain in the file structure

## File Size Optimization

The tool often produces files **smaller** than the original because:
- Removes unwanted content (redacted text)
- Applies advanced compression (qpdf)
- Optimizes images and streams
- Cleans up PDF structure

## Dependencies

- **PyMuPDF (fitz)**: PDF manipulation and redaction
- **qpdf**: PDF optimization and compression
- **uv**: Python package management

## Project Structure

```
pdf-redact-demo/
├── main.py                    # Main redaction script
├── README.md                  # This file
├── pyproject.toml            # uv project configuration
└── *.pdf                     # Your PDF files
```

## Error Handling

The script includes comprehensive error handling:
- ✅ Validates file existence
- ✅ Clear usage instructions
- ✅ Helpful error messages
- ✅ Graceful failure modes

## Contributing

Feel free to submit issues and pull requests to improve the tool!

## License

This project is open source. Use responsibly and ensure you have rights to modify any PDFs you process.
