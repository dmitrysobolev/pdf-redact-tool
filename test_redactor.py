#!/usr/bin/env python3
"""
Basic tests for the PDF redaction tool.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from pdf_redactor import PDFRedactor, RedactionError


class TestPDFRedactor(unittest.TestCase):
    """Test cases for PDFRedactor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.pdf"
        
        # Create a dummy file for testing (not a real PDF)
        self.test_file.write_text("dummy content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_file.exists():
            self.test_file.unlink()
        self.temp_dir.rmdir()
    
    def test_init_with_existing_file(self):
        """Test initialization with existing file."""
        redactor = PDFRedactor(self.test_file)
        self.assertEqual(redactor.input_file, self.test_file)
        self.assertTrue(str(redactor.output_file).endswith("_redacted.pdf"))
    
    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.pdf"
        with self.assertRaises(FileNotFoundError):
            PDFRedactor(nonexistent_file)
    
    def test_output_filename_generation(self):
        """Test output filename generation."""
        redactor = PDFRedactor(self.test_file)
        expected = self.temp_dir / "test_redacted.pdf"
        self.assertEqual(redactor.output_file, expected)
    
    def test_custom_output_file(self):
        """Test custom output file specification."""
        custom_output = self.temp_dir / "custom_output.pdf"
        redactor = PDFRedactor(self.test_file, custom_output)
        self.assertEqual(redactor.output_file, custom_output)
    
    @patch('pdf_redactor.pymupdf.open')
    def test_find_and_redact_text_mock(self, mock_open):
        """Test find_and_redact_text with mocked PyMuPDF."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_page = Mock()
        
        # Set up mock document behavior
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_page.search_for.return_value = [Mock()]  # One instance found
        mock_open.return_value = mock_doc
        
        redactor = PDFRedactor(self.test_file)
        
        with patch.object(redactor, '_save_and_optimize'):
            result = redactor.find_and_redact_text(["test pattern"])
        
        self.assertEqual(result, 1)
        mock_page.add_redact_annot.assert_called_once()
        mock_page.apply_redactions.assert_called_once()


class TestMainFunction(unittest.TestCase):
    """Test cases for main CLI function."""
    
    @patch('sys.argv', ['main.py', '--help'])
    def test_help_argument(self):
        """Test that help argument works."""
        from main import parse_arguments
        with self.assertRaises(SystemExit):
            parse_arguments()


if __name__ == '__main__':
    unittest.main() 