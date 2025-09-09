"""
Merge command implementation.

This module implements the merge command that combines multiple log files
chronologically while maintaining proper ordering and supporting various options.
"""

from typing import Optional

from pogtool.core.interfaces import Command
from pogtool.formatters.text import TextFormatter
from pogtool.parsers.generic import GenericLogParser
from pogtool.parsers.common import CommonLogParser
from pogtool.processors import StandardLogProcessor
from pogtool.readers import MultiFileReader


class MergeCommand(Command):
    """
    Command for merging multiple log files chronologically.
    
    Supports various merge options including source tagging, deduplication,
    timestamp normalization, and streaming output to files or stdout.
    """
    
    def __init__(self) -> None:
        """Initialize the merge command with default dependencies."""
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
        output: Optional[str],
        tag: bool,
        normalize_timestamps: bool,
        deduplicate: bool,
        follow: bool,
        compressed: bool,
    ) -> None:
        """
        Execute the merge command with given arguments.
        
        Args:
            files: Tuple of file paths to merge
            output: Output file path (None for stdout)
            tag: Add source filename as tag to each entry
            normalize_timestamps: Normalize timestamps to standard format
            deduplicate: Remove duplicate entries
            follow: Stream mode for continuously merging growing files
            compressed: Support compressed input files
        """
        if not files:
            print("Error: No input files specified")
            return
        
        if len(files) < 2:
            print("Error: At least two files are required for merging")
            return
        
        try:
            if follow:
                self._merge_follow_mode(
                    list(files), output, tag, deduplicate
                )
            else:
                self._merge_static_files(
                    list(files), output, tag, normalize_timestamps, deduplicate
                )
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nStopped by user")
        except Exception as e:
            print(f"Error: {e}")
    
    def _merge_static_files(
        self,
        files: list[str],
        output: Optional[str],
        tag: bool,
        normalize_timestamps: bool,
        deduplicate: bool,
    ) -> None:
        """
        Merge files in static mode (read all content once).
        
        Args:
            files: List of files to merge
            output: Output file path
            tag: Whether to tag entries with source
            normalize_timestamps: Whether to normalize timestamps
            deduplicate: Whether to remove duplicates
        """
        # Parse all files into separate iterators
        entry_iterators = []
        
        for file_path in files:
            entries = list(self._parse_files([file_path], follow=False))
            entry_iterators.append(iter(entries))
        
        # Merge entries chronologically
        merge_options = {
            'tag_source': tag,
            'deduplicate': deduplicate,
        }
        
        merged_entries = self._log_processor.merge_entries(
            entry_iterators, 
            **merge_options
        )
        
        # Output merged entries
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                for entry in merged_entries:
                    formatted_line = self._format_entry(entry, normalize_timestamps)
                    f.write(formatted_line + '\n')
            print(f"Merged {len(files)} files into {output}")
        else:
            for entry in merged_entries:
                formatted_line = self._format_entry(entry, normalize_timestamps)
                print(formatted_line)
    
    def _merge_follow_mode(
        self,
        files: list[str],
        output: Optional[str],
        tag: bool,
        deduplicate: bool,
    ) -> None:
        """
        Merge files in follow mode (continuously monitor for new entries).
        
        Args:
            files: List of files to follow
            output: Output file path
            tag: Whether to tag entries with source
            deduplicate: Whether to remove duplicates
        """
        import time
        from collections import deque
        
        print(f"Following {len(files)} files for new entries (Ctrl+C to stop)...")
        
        # Keep track of last read positions
        file_positions = {file_path: 0 for file_path in files}
        seen_entries = set() if deduplicate else None
        
        # Open output file if specified
        output_file = None
        if output:
            output_file = open(output, 'w', encoding='utf-8')
        
        try:
            while True:
                new_entries = []
                
                # Check each file for new content
                for file_path in files:
                    try:
                        entries = list(self._parse_files([file_path], follow=False))
                        
                        # Get only new entries since last check
                        current_count = len(entries)
                        last_position = file_positions.get(file_path, 0)
                        
                        if current_count > last_position:
                            new_file_entries = entries[last_position:]
                            
                            for entry in new_file_entries:
                                # Tag with source if requested
                                if tag:
                                    from dataclasses import replace
                                    entry = replace(entry, message=f"[{file_path}] {entry.message}")
                                
                                # Check for duplicates
                                if deduplicate and seen_entries is not None:
                                    entry_key = entry.normalized_message
                                    if entry_key in seen_entries:
                                        continue
                                    seen_entries.add(entry_key)
                                
                                new_entries.append(entry)
                            
                            file_positions[file_path] = current_count
                    
                    except Exception as e:
                        print(f"Warning: Error reading {file_path}: {e}")
                
                # Sort new entries by timestamp and output
                if new_entries:
                    # Sort by timestamp (entries without timestamps go to end)
                    new_entries.sort(
                        key=lambda e: e.timestamp.timestamp() if e.timestamp else float('inf')
                    )
                    
                    for entry in new_entries:
                        formatted_line = self._format_entry(entry, False)
                        
                        if output_file:
                            output_file.write(formatted_line + '\n')
                            output_file.flush()
                        else:
                            print(formatted_line)
                
                time.sleep(0.5)  # Check every 500ms
                
        finally:
            if output_file:
                output_file.close()
    
    def _format_entry(self, entry, normalize_timestamps: bool) -> str:
        """
        Format a log entry for output.
        
        Args:
            entry: LogEntry to format
            normalize_timestamps: Whether to normalize timestamp format
            
        Returns:
            Formatted string
        """
        if normalize_timestamps and entry.timestamp:
            # Use normalized timestamp format
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            level_str = f"[{entry.level.name}]" if entry.level else ""
            parts = [timestamp_str, level_str, entry.message or entry.raw_line]
            return " ".join(filter(None, parts))
        else:
            # Use original raw line
            return entry.raw_line