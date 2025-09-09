"""
File readers for different file types and reading strategies.

This module contains concrete implementations for reading log files
with support for compression, streaming, and following files.
"""

import gzip
import time
from pathlib import Path
from typing import Iterator

from pogtool.core.interfaces import FileReader


class StandardFileReader(FileReader):
    """Standard file reader for regular text files."""
    
    def read_lines(self, file_path: str, follow: bool = False) -> Iterator[str]:
        """
        Read lines from a file.
        
        Args:
            file_path: Path to the file to read
            follow: Whether to follow the file for new lines (like tail -f)
            
        Yields:
            Lines from the file
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Read existing content
            for line in f:
                yield line
            
            # Follow mode: keep reading new lines
            if follow:
                f.seek(0, 2)  # Seek to end of file
                while True:
                    line = f.readline()
                    if line:
                        yield line
                    else:
                        time.sleep(0.1)  # Short sleep to avoid busy waiting
    
    def supports_compression(self) -> bool:
        """Whether this reader supports compressed files."""
        return False


class CompressedFileReader(FileReader):
    """File reader that supports gzip compressed files."""
    
    def read_lines(self, file_path: str, follow: bool = False) -> Iterator[str]:
        """
        Read lines from a potentially compressed file.
        
        Args:
            file_path: Path to the file to read
            follow: Whether to follow the file for new lines (not supported for compressed)
            
        Yields:
            Lines from the file
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if follow:
            raise NotImplementedError("Follow mode is not supported for compressed files")
        
        # Determine if file is compressed by extension or magic bytes
        is_compressed = (
            file_path.endswith('.gz') or 
            file_path.endswith('.gzip') or
            self._is_gzip_file(file_path)
        )
        
        if is_compressed:
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='replace') as f:
                for line in f:
                    yield line
        else:
            # Fall back to standard reading
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    yield line
    
    def supports_compression(self) -> bool:
        """Whether this reader supports compressed files."""
        return True
    
    def _is_gzip_file(self, file_path: str) -> bool:
        """
        Check if file is gzip compressed by reading magic bytes.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file appears to be gzip compressed
        """
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(2)
                return magic == b'\x1f\x8b'
        except (OSError, IOError):
            return False


class MultiFileReader(FileReader):
    """
    File reader that can handle multiple files and different compression types.
    
    Automatically detects compressed files and uses appropriate reading strategy.
    """
    
    def __init__(self) -> None:
        """Initialize with both standard and compressed readers."""
        self._standard_reader = StandardFileReader()
        self._compressed_reader = CompressedFileReader()
    
    def read_lines(self, file_path: str, follow: bool = False) -> Iterator[str]:
        """
        Read lines from a file, auto-detecting compression.
        
        Args:
            file_path: Path to the file to read
            follow: Whether to follow the file for new lines
            
        Yields:
            Lines from the file
        """
        # Check if file appears to be compressed
        if self._is_compressed_file(file_path):
            if follow:
                # Can't follow compressed files, so fall back to standard reader
                yield from self._standard_reader.read_lines(file_path, follow=False)
            else:
                yield from self._compressed_reader.read_lines(file_path, follow=False)
        else:
            yield from self._standard_reader.read_lines(file_path, follow=follow)
    
    def supports_compression(self) -> bool:
        """Whether this reader supports compressed files."""
        return True
    
    def _is_compressed_file(self, file_path: str) -> bool:
        """
        Check if file is compressed based on extension or content.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file appears to be compressed
        """
        # Check by extension first
        compressed_extensions = {'.gz', '.gzip', '.bz2', '.xz'}
        path = Path(file_path)
        if path.suffix.lower() in compressed_extensions:
            return True
        
        # Check by magic bytes for gzip
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(2)
                return magic == b'\x1f\x8b'
        except (OSError, IOError):
            return False