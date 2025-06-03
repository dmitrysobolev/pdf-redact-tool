import pymupdf
import re
import subprocess
import os
import sys
import tempfile

if len(sys.argv) != 3:
    print("Usage: python main.py <pdf_filename> <text_to_redact>")
    print('Example: python main.py document.pdf "Licensed to John Doe <john.doe@example.com>"')
    sys.exit(1)

input_file = sys.argv[1]
text_to_redact = sys.argv[2]

if not os.path.exists(input_file):
    print(f"Error: File '{input_file}' not found!")
    sys.exit(1)

base_name = os.path.splitext(input_file)[0]
output_file = f"{base_name}_redacted.pdf"

print(f"Processing: {input_file}")
print(f"Text to redact: '{text_to_redact}'")
print(f"Output will be: {output_file}")

# Step 1: Redact with PyMuPDF
print("Step 1: Performing redaction...")
doc = pymupdf.open(input_file)

total_found = 0

for page_num in range(len(doc)):
    page = doc[page_num]
    
    text_instances = page.search_for(text_to_redact, flags=pymupdf.TEXT_DEHYPHENATE)
    
    if text_instances:
        print(f"  Found on page {page_num + 1}: {len(text_instances)} instance(s)")
        total_found += len(text_instances)
    
    for inst in text_instances:
        page.add_redact_annot(inst)
    
    page.apply_redactions()

print(f"Total instances found and redacted: {total_found}")

# Use context manager for temporary file to ensure cleanup
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
    temp_filename = temp_file.name
    doc.save(temp_filename, garbage=4, deflate=True, clean=True)
    doc.close()

    # Step 2: Compress with qpdf
    print("Step 2: Optimizing with qpdf...")
    
    try:
        result = subprocess.run([
            "qpdf", 
            "--compress-streams=y",
            "--recompress-flate", 
            "--optimize-images",
            "--object-streams=generate",
            temp_filename,
            output_file
        ])

        # Handle qpdf exit codes gracefully
        # 0 = Success, no issues
        # 2 = Error (recoverable)  
        # 3 = Success with warnings
        # >3 = Fatal error
        if result.returncode == 0:
            print("  qpdf optimization completed successfully")
        elif result.returncode == 3:
            print("  qpdf optimization completed with warnings (this is normal)")
        elif result.returncode == 2:
            print("  qpdf encountered recoverable errors but completed")
        else:
            print(f"  qpdf failed with exit code {result.returncode}")
            raise subprocess.CalledProcessError(result.returncode, result.args)

    finally:
        # Ensure temp file is always cleaned up, even if qpdf fails
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

print(f"Redaction completed: {output_file}")

original_size = os.path.getsize(input_file)
final_size = os.path.getsize(output_file)

print(f"Original size: {original_size / (1024*1024):.1f} MB")
print(f"Final size: {final_size / (1024*1024):.1f} MB")
print(f"Size change: {((final_size - original_size) / original_size * 100):+.1f}%") 