"""
Configuration module for PDF redaction tool.

Handles configuration settings, defaults, and validation.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class RedactionConfig:
    """Configuration settings for PDF redaction."""
    
    # Search behavior
    case_sensitive: bool = True
    use_regex: bool = False
    whole_words_only: bool = False
    
    # Output settings
    output_suffix: str = "_redacted"
    create_backup: bool = False
    backup_suffix: str = ".backup"
    
    # qpdf optimization settings
    compress_streams: bool = True
    recompress_flate: bool = True
    optimize_images: bool = True
    object_streams: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance settings
    max_file_size_mb: Optional[int] = None
    temp_dir: Optional[str] = None
    
    # Pattern sets for common redaction tasks
    pattern_sets: Dict[str, List[str]] = None
    
    def __post_init__(self):
        """Initialize default pattern sets if not provided."""
        if self.pattern_sets is None:
            self.pattern_sets = {
                "email": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
                "phone": [r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"],
                "ssn": [r"\b\d{3}-\d{2}-\d{4}\b"],
                "credit_card": [r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"],
                "license_text": [r"Licensed to.*"],
            }
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'RedactionConfig':
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_data = asdict(self)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_pattern_set(self, name: str) -> List[str]:
        """Get a predefined pattern set by name."""
        if name not in self.pattern_sets:
            available = list(self.pattern_sets.keys())
            raise ValueError(f"Pattern set '{name}' not found. Available: {available}")
        
        return self.pattern_sets[name]
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        if self.max_file_size_mb is not None and self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.temp_dir and not Path(self.temp_dir).exists():
            raise ValueError(f"Temp directory does not exist: {self.temp_dir}")


def create_default_config() -> RedactionConfig:
    """Create a default configuration."""
    return RedactionConfig()


def load_config(config_path: Optional[Path] = None) -> RedactionConfig:
    """
    Load configuration from file or create default.
    
    Args:
        config_path: Path to config file. If None, looks for default locations.
        
    Returns:
        RedactionConfig instance
    """
    if config_path is None:
        # Look for config in default locations
        default_locations = [
            Path.cwd() / "redaction_config.json",
            Path.home() / ".pdf_redactor" / "config.json",
        ]
        
        for location in default_locations:
            if location.exists():
                config_path = location
                break
    
    if config_path and config_path.exists():
        return RedactionConfig.from_file(config_path)
    else:
        return create_default_config()


def get_qpdf_args(config: RedactionConfig) -> List[str]:
    """Generate qpdf command line arguments from configuration."""
    args = ["qpdf"]
    
    if config.compress_streams:
        args.append("--compress-streams=y")
    
    if config.recompress_flate:
        args.append("--recompress-flate")
    
    if config.optimize_images:
        args.append("--optimize-images")
    
    if config.object_streams:
        args.append("--object-streams=generate")
    
    return args 