"""
JSON formatter for machine-readable output.

This formatter provides JSON output for log analysis results,
making them suitable for consumption by other tools and scripts.
"""

import json
from typing import List, Dict, Any

from pogtool.core.interfaces import LogFormatter
from pogtool.core.models import StatsSummary, ComparisonResult, LogEntry


class JsonFormatter(LogFormatter):
    """Formatter for JSON output."""
    
    def __init__(self, indent: int = 2) -> None:
        """
        Initialize the JSON formatter.
        
        Args:
            indent: Number of spaces for JSON indentation
        """
        self.indent = indent
    
    def format_stats(self, stats: StatsSummary, show_levels: bool = True, show_patterns: bool = True, show_top: bool = True, show_time_groups: bool = True) -> str:
        """
        Format statistics summary as JSON.
        
        Args:
            stats: Statistics summary to format
            show_levels: Whether to include level counts
            show_patterns: Whether to include pattern counts
            show_top: Whether to include top messages
            show_time_groups: Whether to include time groups
            
        Returns:
            JSON string
        """
        data = stats.to_dict()
        
        # Remove sections based on flags
        if not show_levels:
            data.pop("level_counts", None)
        if not show_patterns:
            data.pop("pattern_counts", None)
        if not show_top:
            data.pop("top_messages", None)
        if not show_time_groups:
            data.pop("time_groups", None)
            
        return json.dumps(data, indent=self.indent, ensure_ascii=False)
    
    def format_comparison(self, result: ComparisonResult) -> str:
        """
        Format comparison result as JSON.
        
        Args:
            result: Comparison result to format
            
        Returns:
            JSON string
        """
        data = {
            "summary": {
                "added_lines": len(result.added_lines),
                "removed_lines": len(result.removed_lines),
                "modified_lines": len(result.modified_lines),
                "common_lines": len(result.common_lines),
                "total_differences": result.total_differences,
                "has_differences": result.has_differences,
            },
            "details": {
                "added_lines": [self._entry_to_dict(entry) for entry in result.added_lines],
                "removed_lines": [self._entry_to_dict(entry) for entry in result.removed_lines],
                "modified_lines": [
                    {
                        "old": self._entry_to_dict(old_entry),
                        "new": self._entry_to_dict(new_entry)
                    }
                    for old_entry, new_entry in result.modified_lines
                ],
                "common_lines": [self._entry_to_dict(entry) for entry in result.common_lines],
            }
        }
        
        return json.dumps(data, indent=self.indent, ensure_ascii=False)
    
    def format_entries(self, entries: List[LogEntry]) -> str:
        """
        Format log entries as JSON.
        
        Args:
            entries: Log entries to format
            
        Returns:
            JSON string
        """
        data = {
            "entries": [self._entry_to_dict(entry) for entry in entries],
            "total_count": len(entries)
        }
        
        return json.dumps(data, indent=self.indent, ensure_ascii=False)
    
    def _entry_to_dict(self, entry: LogEntry) -> Dict[str, Any]:
        """
        Convert a LogEntry to a dictionary for JSON serialization.
        
        Args:
            entry: LogEntry to convert
            
        Returns:
            Dictionary representation
        """
        result = {
            "raw_line": entry.raw_line,
            "message": entry.message,
        }
        
        if entry.timestamp:
            result["timestamp"] = entry.timestamp.isoformat()
        
        if entry.level:
            result["level"] = entry.level.name
        
        if entry.source_file:
            result["source_file"] = entry.source_file
        
        if entry.line_number:
            result["line_number"] = entry.line_number
        
        if entry.extra_fields:
            result["extra_fields"] = entry.extra_fields
        
        return result