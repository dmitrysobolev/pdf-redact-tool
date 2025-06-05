#!/usr/bin/env python3
"""
PDF Redaction Tool - Command Line Interface

A comprehensive tool for redacting text from PDF files with optimization.
Supports regex patterns, case-insensitive matching, and configurable options.
"""

import argparse
import logging
import sys
from pathlib import Path

from pdf_redactor import PDFRedactor, RedactionError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Redact text from PDF files with optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf "John Doe"
  %(prog)s -o output.pdf document.pdf "Licensed to.*"
  %(prog)s --regex --case-insensitive document.pdf "confidential"
  %(prog)s --multiple-patterns document.pdf "pattern1" "pattern2"
        """
    )
    
    parser.add_argument("input_file", type=Path, help="Input PDF file")
    parser.add_argument("patterns", nargs="+", help="Text patterns to redact")
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: input_file_redacted.pdf)"
    )
    
    parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat patterns as regular expressions"
    )
    
    parser.add_argument(
        "--case-insensitive",
        action="store_true",
        help="Perform case-insensitive matching"
    )
    
    parser.add_argument(
        "--whole-words",
        action="store_true",
        help="Match whole words only"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be redacted without making changes"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        redactor = PDFRedactor(args.input_file, args.output, show_progress=not args.no_progress)
        
        logger.info(f"Processing: {args.input_file}")
        logger.info(f"Patterns to redact: {args.patterns}")
        logger.info(f"Output will be: {redactor.output_file}")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            preview = redactor.preview_redactions(
                args.patterns,
                case_sensitive=not args.case_insensitive,
                use_regex=args.regex,
                whole_words_only=args.whole_words
            )
            
            logger.info("Preview Results:")
            for pattern, info in preview["patterns"].items():
                logger.info(f"  Pattern '{pattern}': {info['count']} instances on pages {info['pages']}")
            
            logger.info(f"Total instances that would be redacted: {preview['total_instances']}")
            logger.info(f"Pages that would be affected: {preview['pages_affected']}")
            return 0
        
        total_redacted = redactor.find_and_redact_text(
            args.patterns,
            case_sensitive=not args.case_insensitive,
            use_regex=args.regex,
            whole_words_only=args.whole_words
        )
        
        logger.info(f"Total instances redacted: {total_redacted}")
        
        if total_redacted == 0:
            logger.warning("No instances found to redact")
        
        original_mb, final_mb, size_change = redactor.get_size_info()
        logger.info(f"Original size: {original_mb:.1f} MB")
        logger.info(f"Final size: {final_mb:.1f} MB")
        logger.info(f"Size change: {size_change:+.1f}%")
        
        logger.info(f"Redaction completed: {redactor.output_file}")
        return 0
        
    except (FileNotFoundError, RedactionError) as e:
        logger.error(str(e))
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 