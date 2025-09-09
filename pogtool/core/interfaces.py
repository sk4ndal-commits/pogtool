"""
Core interfaces and abstract base classes for pogtool.

This module defines the contracts and abstractions that enable
dependency inversion and testability throughout the application.
"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Dict, Any, Optional, TextIO

from pogtool.core.models import LogEntry, StatsSummary, ComparisonResult


class FileReader(ABC):
    """Abstract interface for reading files with different strategies."""
    
    @abstractmethod
    def read_lines(self, file_path: str, follow: bool = False) -> Iterator[str]:
        """
        Read lines from a file.
        
        Args:
            file_path: Path to the file to read
            follow: Whether to follow the file for new lines (like tail -f)
            
        Yields:
            Lines from the file
        """
        pass
    
    @abstractmethod
    def supports_compression(self) -> bool:
        """Whether this reader supports compressed files."""
        pass


class LogParser(ABC):
    """Abstract interface for parsing log entries from raw text."""
    
    @abstractmethod
    def parse_line(self, line: str, source_file: Optional[str] = None, line_number: Optional[int] = None) -> LogEntry:
        """
        Parse a single log line into a LogEntry.
        
        Args:
            line: Raw log line text
            source_file: Optional source file path
            line_number: Optional line number in source file
            
        Returns:
            Parsed LogEntry object
        """
        pass
    
    @abstractmethod
    def can_parse_format(self, sample_lines: List[str]) -> bool:
        """
        Determine if this parser can handle the given log format.
        
        Args:
            sample_lines: Sample lines to analyze
            
        Returns:
            True if this parser can handle the format
        """
        pass


class LogFormatter(ABC):
    """Abstract interface for formatting log output."""
    
    @abstractmethod
    def format_stats(self, stats: StatsSummary) -> str:
        """Format statistics summary for output."""
        pass
    
    @abstractmethod
    def format_comparison(self, result: ComparisonResult) -> str:
        """Format comparison result for output."""
        pass
    
    @abstractmethod
    def format_entries(self, entries: List[LogEntry]) -> str:
        """Format log entries for output."""
        pass


class LogProcessor(ABC):
    """Abstract interface for processing log entries."""
    
    @abstractmethod
    def filter_entries(self, entries: Iterator[LogEntry], **filters: Any) -> Iterator[LogEntry]:
        """
        Filter log entries based on criteria.
        
        Args:
            entries: Iterator of log entries to filter
            **filters: Filter criteria (level, patterns, etc.)
            
        Yields:
            Filtered log entries
        """
        pass
    
    @abstractmethod
    def compute_stats(self, entries: Iterator[LogEntry], **options: Any) -> StatsSummary:
        """
        Compute statistics for log entries.
        
        Args:
            entries: Iterator of log entries to analyze
            **options: Analysis options (group_by, top_n, etc.)
            
        Returns:
            Statistics summary
        """
        pass
    
    @abstractmethod
    def compare_entries(self, entries1: List[LogEntry], entries2: List[LogEntry], **options: Any) -> ComparisonResult:
        """
        Compare two sets of log entries.
        
        Args:
            entries1: First set of entries
            entries2: Second set of entries
            **options: Comparison options (ignore_timestamps, fuzzy, etc.)
            
        Returns:
            Comparison result
        """
        pass
    
    @abstractmethod
    def merge_entries(self, entry_iterators: List[Iterator[LogEntry]], **options: Any) -> Iterator[LogEntry]:
        """
        Merge multiple iterators of log entries chronologically.
        
        Args:
            entry_iterators: List of entry iterators to merge
            **options: Merge options (deduplicate, tag, etc.)
            
        Yields:
            Merged log entries in chronological order
        """
        pass


class Command(ABC):
    """Abstract base class for all commands."""
    
    def __init__(self, file_reader: Optional[FileReader] = None, 
                 log_parser: Optional[LogParser] = None,
                 log_formatter: Optional[LogFormatter] = None,
                 log_processor: Optional[LogProcessor] = None) -> None:
        """
        Initialize command with dependencies.
        
        Args:
            file_reader: File reading strategy
            log_parser: Log parsing strategy  
            log_formatter: Output formatting strategy
            log_processor: Log processing strategy
        """
        self._file_reader = file_reader
        self._log_parser = log_parser  
        self._log_formatter = log_formatter
        self._log_processor = log_processor
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> None:
        """
        Execute the command with given arguments.
        
        Args:
            **kwargs: Command-specific arguments
        """
        pass
    
    def _parse_files(self, file_paths: List[str], follow: bool = False) -> Iterator[LogEntry]:
        """
        Helper method to parse multiple files into log entries.
        
        Args:
            file_paths: List of file paths to parse
            follow: Whether to follow files for new content
            
        Yields:
            Parsed log entries
        """
        if not self._file_reader or not self._log_parser:
            raise RuntimeError("FileReader and LogParser must be provided")
            
        for file_path in file_paths:
            line_number = 0
            for line in self._file_reader.read_lines(file_path, follow=follow):
                line_number += 1
                if line.strip():  # Skip empty lines
                    yield self._log_parser.parse_line(line, source_file=file_path, line_number=line_number)
    
    def _write_output(self, content: str, output_path: Optional[str]) -> None:
        """
        Helper method to write content to file or stdout.
        
        Args:
            content: Content to write
            output_path: Output file path, or None for stdout
        """
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            print(content)


class OutputWriter(ABC):
    """Abstract interface for writing output to different destinations."""
    
    @abstractmethod
    def write(self, content: str) -> None:
        """Write content to the destination."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered content."""
        pass


class StdoutWriter(OutputWriter):
    """Writer that outputs to stdout."""
    
    def write(self, content: str) -> None:
        print(content, end='')
    
    def flush(self) -> None:
        import sys
        sys.stdout.flush()


class FileWriter(OutputWriter):
    """Writer that outputs to a file."""
    
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._file: Optional[TextIO] = None
    
    def write(self, content: str) -> None:
        if self._file is None:
            self._file = open(self.file_path, 'w', encoding='utf-8')
        self._file.write(content)
    
    def flush(self) -> None:
        if self._file:
            self._file.flush()
    
    def __del__(self) -> None:
        if self._file:
            self._file.close()