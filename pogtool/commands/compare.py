"""
Compare command implementation.

This module implements the comparison command that compares two log files
and shows differences, additions, and removals with various output options.
"""

from typing import Optional

from pogtool.core.interfaces import Command
from pogtool.formatters.text import TextFormatter
from pogtool.formatters.json import JsonFormatter
from pogtool.parsers.generic import GenericLogParser
from pogtool.processors import StandardLogProcessor
from pogtool.readers import MultiFileReader


class CompareCommand(Command):
    """
    Command for comparing two log files and showing differences.
    
    Supports various comparison options including ignoring timestamps,
    filtering by log level, colorized output, and fuzzy matching.
    """
    
    def __init__(self) -> None:
        """Initialize the compare command with default dependencies."""
        file_reader = MultiFileReader()
        log_parser = GenericLogParser()
        log_processor = StandardLogProcessor()
        log_formatter = TextFormatter()
        
        super().__init__(
            file_reader=file_reader,
            log_parser=log_parser,
            log_formatter=log_formatter,
            log_processor=log_processor,
        )
    
    def execute(
        self,
        file1: str,
        file2: str,
        only: Optional[str],
        ignore_timestamps: bool,
        color: bool,
        summary: bool,
        output_json: bool,
        fuzzy: bool,
    ) -> None:
        """
        Execute the compare command with given arguments.
        
        Args:
            file1: Path to first file to compare
            file2: Path to second file to compare
            only: Filter to only this log level
            ignore_timestamps: Ignore timestamps when comparing
            color: Use colorized output
            summary: Show only summary statistics
            output_json: Output in JSON format
            fuzzy: Use fuzzy matching (ignore whitespace differences)
        """
        try:
            # Parse both files into log entries
            entries1 = list(self._parse_files([file1], follow=False))
            entries2 = list(self._parse_files([file2], follow=False))
            
            if not entries1 and not entries2:
                print("No log entries found in either file")
                return
            
            # Apply filtering if specified
            if only:
                entries1 = list(
                    self._log_processor.filter_entries(
                        iter(entries1), 
                        level=only
                    )
                )
                entries2 = list(
                    self._log_processor.filter_entries(
                        iter(entries2), 
                        level=only
                    )
                )
            
            # Prepare comparison options
            comparison_options = {
                'ignore_timestamps': ignore_timestamps,
                'fuzzy': fuzzy,
            }
            
            # Perform comparison
            result = self._log_processor.compare_entries(
                entries1, 
                entries2, 
                **comparison_options
            )
            
            # Choose appropriate formatter
            formatter = self._get_formatter(output_json, color)
            
            # Show summary or full results
            if summary:
                self._show_summary(result)
            else:
                output = formatter.format_comparison(result)
                print(output)
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    
    def _get_formatter(self, output_json: bool, color: bool) -> object:
        """
        Get the appropriate formatter based on output options.
        
        Args:
            output_json: Whether to use JSON output
            color: Whether to use colored output
            
        Returns:
            Appropriate formatter instance
        """
        if output_json:
            return JsonFormatter()
        else:
            return TextFormatter(use_colors=color)
    
    def _show_summary(self, result) -> None:
        """
        Show a brief summary of comparison results.
        
        Args:
            result: Comparison result to summarize
        """
        print("Comparison Summary:")
        print("=" * 30)
        print(f"Added lines:     {len(result.added_lines):>6}")
        print(f"Removed lines:   {len(result.removed_lines):>6}")
        print(f"Modified lines:  {len(result.modified_lines):>6}")
        print(f"Common lines:    {len(result.common_lines):>6}")
        print("-" * 30)
        print(f"Total differences: {result.total_differences:>4}")
        
        if result.has_differences:
            print("\nFiles are different")
        else:
            print("\nFiles are identical")