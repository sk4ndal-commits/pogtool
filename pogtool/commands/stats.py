"""
Stats command implementation.

This module implements the statistics command that analyzes log files
and generates comprehensive statistics including counts, patterns, and trends.
"""

from typing import Optional

from pogtool.core.interfaces import Command
from pogtool.core.models import TimeInterval
from pogtool.formatters.text import TextFormatter
from pogtool.formatters.json import JsonFormatter
from pogtool.formatters.csv import CsvFormatter
from pogtool.parsers.generic import GenericLogParser
from pogtool.parsers.common import CommonLogParser
from pogtool.processors import StandardLogProcessor
from pogtool.readers import MultiFileReader


class StatsCommand(Command):
    """
    Command for analyzing log files and generating statistics.
    
    Supports various analysis options including level counting, pattern matching,
    time grouping, top messages, and multiple output formats.
    """
    
    def __init__(self) -> None:
        """Initialize the stats command with default dependencies."""
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
        files: tuple[str, ...],
        levels: bool,
        patterns: tuple[str, ...],
        group_by: Optional[str],
        only: Optional[str],
        top: Optional[int],
        output_json: bool,
        output_csv: bool,
        follow: bool,
        normalize_timestamps: bool,
    ) -> None:
        """
        Execute the stats command with given arguments.
        
        Args:
            files: Tuple of file paths to analyze
            levels: Whether to count log levels
            patterns: Patterns to search for and count
            group_by: Time interval for grouping (minute/hour/day)
            only: Filter to only this log level
            top: Number of top messages to show
            output_json: Output in JSON format
            output_csv: Output in CSV format
            follow: Follow files for new content (live mode)
            normalize_timestamps: Normalize timestamps to standard format
        """
        if not files:
            print("Error: No input files specified")
            return
        
        try:
            # Parse all files into log entries
            entries = list(self._parse_files(list(files), follow=follow))
            
            if not entries:
                print("No log entries found in the specified files")
                return
            
            # Apply filtering if specified
            if only:
                entries = list(
                    self._log_processor.filter_entries(
                        iter(entries), 
                        level=only
                    )
                )
            
            # Prepare analysis options
            analysis_options = {}
            
            if group_by:
                analysis_options['group_by'] = group_by
            
            if top:
                analysis_options['top_n'] = top
            
            if patterns:
                analysis_options['patterns'] = list(patterns)
            
            # Compute statistics
            stats = self._log_processor.compute_stats(iter(entries), **analysis_options)
            
            # Choose appropriate formatter
            formatter = self._get_formatter(output_json, output_csv)
            
            # Determine which sections to show based on flags
            show_levels = levels
            show_patterns = bool(patterns)
            show_top = top is not None
            show_time_groups = group_by is not None
            
            # If no specific flags are set, show all sections (backward compatibility)
            if not any([show_levels, show_patterns, show_top, show_time_groups]):
                show_levels = show_patterns = show_top = show_time_groups = True
            
            # If --only flag is used, suppress Top Messages (show only levels)
            if only:
                show_top = False
            
            # Format and output results
            if output_csv:
                # CSV formatter doesn't support selective sections yet
                output = formatter.format_stats(stats)
            else:
                output = formatter.format_stats(stats, show_levels, show_patterns, show_top, show_time_groups)
            print(output)
            
            # In follow mode, keep monitoring and updating stats
            if follow:
                print("\n--- Following files for new entries (Ctrl+C to stop) ---")
                self._follow_mode(list(files), analysis_options, formatter)
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nStopped by user")
        except Exception as e:
            print(f"Error: {e}")
    
    def _get_formatter(self, output_json: bool, output_csv: bool) -> object:
        """
        Get the appropriate formatter based on output options.
        
        Args:
            output_json: Whether to use JSON output
            output_csv: Whether to use CSV output
            
        Returns:
            Appropriate formatter instance
        """
        if output_json:
            return JsonFormatter()
        elif output_csv:
            return CsvFormatter()
        else:
            return TextFormatter(use_colors=True)
    
    def _follow_mode(self, files: list[str], analysis_options: dict, formatter: object) -> None:
        """
        Run in follow mode, continuously updating statistics.
        
        Args:
            files: List of files to follow
            analysis_options: Analysis configuration
            formatter: Output formatter to use
        """
        import time
        
        try:
            last_stats = None
            
            while True:
                # Re-parse files to get latest content
                entries = list(self._parse_files(files, follow=False))
                
                if entries:
                    # Compute fresh statistics
                    stats = self._log_processor.compute_stats(iter(entries), **analysis_options)
                    
                    # Only update if stats have changed
                    if last_stats is None or stats.to_dict() != last_stats.to_dict():
                        # Clear screen and show updated stats
                        print("\033[2J\033[H")  # ANSI escape codes to clear screen
                        print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(formatter.format_stats(stats))
                        last_stats = stats
                
                time.sleep(1)  # Update every second
                
        except KeyboardInterrupt:
            pass