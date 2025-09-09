"""
CSV formatter for spreadsheet-compatible output.

This formatter provides CSV output for log analysis results,
making them suitable for import into spreadsheets and data analysis tools.
"""

import csv
import io
from typing import List

from pogtool.core.interfaces import LogFormatter
from pogtool.core.models import StatsSummary, ComparisonResult, LogEntry


class CsvFormatter(LogFormatter):
    """Formatter for CSV output."""
    
    def __init__(self, delimiter: str = ',', quotechar: str = '"') -> None:
        """
        Initialize the CSV formatter.
        
        Args:
            delimiter: CSV field delimiter
            quotechar: CSV quote character
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
    
    def format_stats(self, stats: StatsSummary) -> str:
        """
        Format statistics summary as CSV.
        
        Args:
            stats: Statistics summary to format
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        # Basic stats
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Lines', stats.total_lines])
        writer.writerow([])  # Empty row
        
        # Log levels
        if stats.level_counts:
            writer.writerow(['Log Level', 'Count'])
            for level, count in sorted(stats.level_counts.items()):
                writer.writerow([level, count])
            writer.writerow([])  # Empty row
        
        # Pattern matches
        if stats.pattern_counts:
            writer.writerow(['Pattern', 'Count'])
            for pattern, count in stats.pattern_counts.items():
                writer.writerow([pattern, count])
            writer.writerow([])  # Empty row
        
        # Time groups
        if stats.time_groups:
            writer.writerow(['Time Group', 'Count'])
            for time_key, count in sorted(stats.time_groups.items()):
                writer.writerow([time_key, count])
            writer.writerow([])  # Empty row
        
        # Top messages
        if stats.top_messages:
            writer.writerow(['Rank', 'Count', 'Message'])
            for i, (message, count) in enumerate(stats.top_messages, 1):
                writer.writerow([i, count, message])
        
        return output.getvalue()
    
    def format_comparison(self, result: ComparisonResult) -> str:
        """
        Format comparison result as CSV.
        
        Args:
            result: Comparison result to format
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        # Summary
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Added Lines', len(result.added_lines)])
        writer.writerow(['Removed Lines', len(result.removed_lines)])
        writer.writerow(['Modified Lines', len(result.modified_lines)])
        writer.writerow(['Common Lines', len(result.common_lines)])
        writer.writerow(['Total Differences', result.total_differences])
        writer.writerow([])  # Empty row
        
        # Detailed differences
        writer.writerow(['Type', 'Timestamp', 'Level', 'Source File', 'Line Number', 'Message'])
        
        # Added lines
        for entry in result.added_lines:
            writer.writerow([
                'ADDED',
                entry.timestamp.isoformat() if entry.timestamp else '',
                entry.level.name if entry.level else '',
                entry.source_file or '',
                entry.line_number or '',
                entry.message or entry.raw_line
            ])
        
        # Removed lines
        for entry in result.removed_lines:
            writer.writerow([
                'REMOVED',
                entry.timestamp.isoformat() if entry.timestamp else '',
                entry.level.name if entry.level else '',
                entry.source_file or '',
                entry.line_number or '',
                entry.message or entry.raw_line
            ])
        
        # Modified lines (old and new as separate rows)
        for old_entry, new_entry in result.modified_lines:
            writer.writerow([
                'MODIFIED_OLD',
                old_entry.timestamp.isoformat() if old_entry.timestamp else '',
                old_entry.level.name if old_entry.level else '',
                old_entry.source_file or '',
                old_entry.line_number or '',
                old_entry.message or old_entry.raw_line
            ])
            writer.writerow([
                'MODIFIED_NEW',
                new_entry.timestamp.isoformat() if new_entry.timestamp else '',
                new_entry.level.name if new_entry.level else '',
                new_entry.source_file or '',
                new_entry.line_number or '',
                new_entry.message or new_entry.raw_line
            ])
        
        return output.getvalue()
    
    def format_entries(self, entries: List[LogEntry]) -> str:
        """
        Format log entries as CSV.
        
        Args:
            entries: Log entries to format
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        # Header
        writer.writerow(['Timestamp', 'Level', 'Source File', 'Line Number', 'Message', 'Raw Line'])
        
        # Entries
        for entry in entries:
            writer.writerow([
                entry.timestamp.isoformat() if entry.timestamp else '',
                entry.level.name if entry.level else '',
                entry.source_file or '',
                entry.line_number or '',
                entry.message or '',
                entry.raw_line
            ])
        
        return output.getvalue()