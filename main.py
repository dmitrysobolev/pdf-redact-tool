import fitz  # PyMuPDF
import re
import subprocess
import os
import sys

# Check if filename and text were provided
if len(sys.argv) != 3:
    print("Usage: python main.py <pdf_filename> <text_to_redact>")
    print('Example: python main.py document.pdf "Licensed to John Doe <john.doe@example.com>"')
    sys.exit(1)

input_file = sys.argv[1]
text_to_redact = sys.argv[2]

# Check if input file exists
if not os.path.exists(input_file):
    print(f"Error: File '{input_file}' not found!")
    sys.exit(1)

# Generate output filename
base_name = os.path.splitext(input_file)[0]
output_file = f"{base_name}_redacted.pdf"

print(f"Processing: {input_file}")
print(f"Text to redact: '{text_to_redact}'")
print(f"Output will be: {output_file}")

# Step 1: Redact with PyMuPDF
print("Step 1: Performing redaction...")
doc = fitz.open(input_file)

total_found = 0

# Iterate through all pages
for page_num in range(len(doc)):
    page = doc[page_num]
    
    # Search for the specified text
    text_instances = page.search_for(text_to_redact, flags=fitz.TEXT_DEHYPHENATE)
    
    if text_instances:
        print(f"  Found on page {page_num + 1}: {len(text_instances)} instance(s)")
        total_found += len(text_instances)
    
    # Redact each instance
    for inst in text_instances:
        page.add_redact_annot(inst)
    
    # Apply redactions
    page.apply_redactions()

print(f"Total instances found and redacted: {total_found}")

# Save temporary file
temp_file = "temp_redacted.pdf"
doc.save(temp_file, garbage=4, deflate=True, clean=True)
doc.close()

# Step 2: Compress with qpdf
print("Step 2: Optimizing with qpdf...")

subprocess.run([
    "qpdf", 
    "--compress-streams=y",
    "--recompress-flate", 
    "--optimize-images",
    "--object-streams=generate",
    temp_file,
    output_file
], check=True)

# Remove temporary file
os.remove(temp_file)

print(f"Redaction completed: {output_file}")

# Show file sizes for comparison
original_size = os.path.getsize(input_file)
final_size = os.path.getsize(output_file)

print(f"Original size: {original_size / (1024*1024):.1f} MB")
print(f"Final size: {final_size / (1024*1024):.1f} MB")
print(f"Size change: {((final_size - original_size) / original_size * 100):+.1f}%") 