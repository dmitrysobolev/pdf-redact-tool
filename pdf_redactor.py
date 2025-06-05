"""
PDF Redaction Module

Contains the core PDFRedactor class for handling PDF redaction operations.
"""

import logging
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple, Iterator

import pymupdf

# Constants
DEFAULT_OUTPUT_SUFFIX = "_redacted"
QPDF_SUCCESS_CODES = {0, 2, 3}  # 0=success, 2=recoverable errors, 3=warnings
MB_DIVISOR = 1024 * 1024


class RedactionError(Exception):
    """Custom exception for redaction-related errors."""
    pass


class PDFRedactor:
    """Handles PDF redaction operations with PyMuPDF and qpdf optimization."""
    
    def __init__(self, input_file: Path, output_file: Optional[Path] = None):
        self.input_file = Path(input_file)
        self.output_file = output_file or self._generate_output_filename()
        self.logger = logging.getLogger(__name__)
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
    
    def _generate_output_filename(self) -> Path:
        """Generate output filename based on input filename."""
        base_name = self.input_file.stem
        suffix = self.input_file.suffix
        return self.input_file.parent / f"{base_name}{DEFAULT_OUTPUT_SUFFIX}{suffix}"
    
    @contextmanager
    def _temp_pdf_file(self) -> Iterator[str]:
        """Context manager for temporary PDF files."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_filename = temp_file.name
        temp_file.close()
        
        try:
            yield temp_filename
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def find_and_redact_text(
        self, 
        text_patterns: List[str], 
        case_sensitive: bool = True,
        use_regex: bool = False,
        whole_words_only: bool = False
    ) -> int:
        """
        Find and redact text patterns in the PDF.
        
        Args:
            text_patterns: List of text patterns to redact
            case_sensitive: Whether search should be case sensitive
            use_regex: Whether to treat patterns as regex
            whole_words_only: Whether to match whole words only
            
        Returns:
            Total number of instances redacted
        """
        self.logger.info(f"Opening PDF: {self.input_file}")
        
        try:
            doc = pymupdf.open(str(self.input_file))
        except Exception as e:
            raise RedactionError(f"Failed to open PDF: {e}")
        
        total_redacted = 0
        
        try:
            for pattern in text_patterns:
                self.logger.info(f"Searching for pattern: '{pattern}'")
                pattern_redacted = self._redact_pattern(
                    doc, pattern, case_sensitive, use_regex, whole_words_only
                )
                total_redacted += pattern_redacted
                self.logger.info(f"Redacted {pattern_redacted} instances of '{pattern}'")
            
            self.logger.info("Applying redactions and optimizing...")
            self._save_and_optimize(doc)
            
        finally:
            doc.close()
        
        return total_redacted
    
    def _redact_pattern(
        self, 
        doc: pymupdf.Document, 
        pattern: str, 
        case_sensitive: bool,
        use_regex: bool,
        whole_words_only: bool
    ) -> int:
        """Redact a specific pattern in the document."""
        pattern_count = 0
        search_flags = pymupdf.TEXT_DEHYPHENATE
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            if use_regex:
                page_instances = self._find_regex_instances(
                    page, pattern, case_sensitive, whole_words_only
                )
            else:
                page_instances = self._find_text_instances(
                    page, pattern, case_sensitive, whole_words_only, search_flags
                )
            
            if page_instances:
                self.logger.debug(f"  Found on page {page_num + 1}: {len(page_instances)} instance(s)")
                pattern_count += len(page_instances)
                
                for instance in page_instances:
                    page.add_redact_annot(instance)
                
                page.apply_redactions()
        
        return pattern_count
    
    def _find_text_instances(
        self, 
        page, 
        pattern: str, 
        case_sensitive: bool, 
        whole_words_only: bool,
        search_flags: int
    ) -> List:
        """Find text instances using PyMuPDF's search."""
        if case_sensitive:
            instances = page.search_for(pattern, flags=search_flags)
        else:
            # For case-insensitive search, we need to get all text and search manually
            instances = self._case_insensitive_search(page, pattern, search_flags)
        
        if whole_words_only:
            instances = self._filter_whole_words(page, instances, pattern)
        
        return instances
    
    def _case_insensitive_search(self, page, pattern: str, search_flags: int) -> List:
        """Perform case-insensitive text search."""
        # Get all text blocks from the page
        text_blocks = page.get_text("dict")
        instances = []
        
        # Search in each text block
        pattern_lower = pattern.lower()
        
        for block in text_blocks.get("blocks", []):
            if "lines" not in block:
                continue
            
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    text_lower = text.lower()
                    
                    # Find all occurrences in this span
                    start = 0
                    while True:
                        pos = text_lower.find(pattern_lower, start)
                        if pos == -1:
                            break
                        
                        # Calculate the bbox for this occurrence
                        bbox = span["bbox"]
                        char_width = (bbox[2] - bbox[0]) / len(text) if text else 0
                        
                        # Estimate position within the span
                        start_x = bbox[0] + pos * char_width
                        end_x = bbox[0] + (pos + len(pattern)) * char_width
                        
                        instances.append((start_x, bbox[1], end_x, bbox[3]))
                        start = pos + 1
        
        return instances
    
    def _find_regex_instances(
        self, 
        page, 
        pattern: str, 
        case_sensitive: bool, 
        whole_words_only: bool
    ) -> List:
        """Find regex pattern instances in the page."""
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        if whole_words_only:
            pattern = r'\b' + pattern + r'\b'
        
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            self.logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return []
        
        # Get text with position information
        text_blocks = page.get_text("dict")
        instances = []
        
        for block in text_blocks.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    bbox = span["bbox"]
                    
                    # Find all matches in this span
                    for match in compiled_pattern.finditer(text):
                        start_pos, end_pos = match.span()
                        
                        # Calculate bbox for the match
                        char_width = (bbox[2] - bbox[0]) / len(text) if text else 0
                        start_x = bbox[0] + start_pos * char_width
                        end_x = bbox[0] + end_pos * char_width
                        
                        instances.append((start_x, bbox[1], end_x, bbox[3]))
        
        return instances
    
    def _filter_whole_words(self, page, instances: List, pattern: str) -> List:
        """Filter instances to only include whole word matches."""
        # This is a simplified implementation
        # In a production system, you'd want to examine the surrounding characters
        filtered_instances = []
        
        for instance in instances:
            # For now, just return all instances
            # TODO: Implement proper word boundary checking
            filtered_instances.append(instance)
        
        return filtered_instances
    
    def _save_and_optimize(self, doc: pymupdf.Document) -> None:
        """Save the document and optimize with qpdf."""
        with self._temp_pdf_file() as temp_filename:
            try:
                doc.save(temp_filename, garbage=4, deflate=True, clean=True)
                self._optimize_with_qpdf(temp_filename)
            except Exception as e:
                raise RedactionError(f"Failed to save or optimize PDF: {e}")
    
    def _optimize_with_qpdf(self, temp_filename: str) -> None:
        """Optimize PDF using qpdf."""
        qpdf_cmd = [
            "qpdf",
            "--compress-streams=y",
            "--recompress-flate",
            "--optimize-images",
            "--object-streams=generate",
            temp_filename,
            str(self.output_file)
        ]
        
        try:
            result = subprocess.run(qpdf_cmd, capture_output=True, text=True)
            
            if result.returncode in QPDF_SUCCESS_CODES:
                if result.returncode == 0:
                    self.logger.info("qpdf optimization completed successfully")
                elif result.returncode == 3:
                    self.logger.info("qpdf optimization completed with warnings")
                elif result.returncode == 2:
                    self.logger.info("qpdf encountered recoverable errors but completed")
            else:
                self.logger.error(f"qpdf failed: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, qpdf_cmd)
                
        except FileNotFoundError:
            raise RedactionError(
                "qpdf not found. Please install qpdf:\n"
                "  macOS: brew install qpdf\n"
                "  Ubuntu: sudo apt-get install qpdf"
            )
    
    def get_size_info(self) -> Tuple[float, float, float]:
        """Get file size information."""
        original_size = self.input_file.stat().st_size
        final_size = self.output_file.stat().st_size
        size_change = ((final_size - original_size) / original_size * 100)
        
        return (
            original_size / MB_DIVISOR,
            final_size / MB_DIVISOR,
            size_change
        )
    
    def preview_redactions(
        self, 
        text_patterns: List[str], 
        case_sensitive: bool = True,
        use_regex: bool = False,
        whole_words_only: bool = False
    ) -> dict:
        """
        Preview what would be redacted without making changes.
        
        Returns:
            Dictionary with pattern counts and page information
        """
        self.logger.info(f"Previewing redactions for: {self.input_file}")
        
        try:
            doc = pymupdf.open(str(self.input_file))
        except Exception as e:
            raise RedactionError(f"Failed to open PDF: {e}")
        
        preview_results = {
            "total_instances": 0,
            "patterns": {},
            "pages_affected": set()
        }
        
        try:
            for pattern in text_patterns:
                pattern_count = 0
                pattern_pages = set()
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    if use_regex:
                        page_instances = self._find_regex_instances(
                            page, pattern, case_sensitive, whole_words_only
                        )
                    else:
                        search_flags = pymupdf.TEXT_DEHYPHENATE
                        page_instances = self._find_text_instances(
                            page, pattern, case_sensitive, whole_words_only, search_flags
                        )
                    
                    if page_instances:
                        page_count = len(page_instances)
                        pattern_count += page_count
                        pattern_pages.add(page_num + 1)
                        preview_results["pages_affected"].add(page_num + 1)
                
                preview_results["patterns"][pattern] = {
                    "count": pattern_count,
                    "pages": sorted(pattern_pages)
                }
                preview_results["total_instances"] += pattern_count
        
        finally:
            doc.close()
        
        preview_results["pages_affected"] = sorted(preview_results["pages_affected"])
        return preview_results 