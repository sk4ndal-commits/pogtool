"""
Text formatter for human-readable output.

This formatter provides clean, readable text output for log analysis results,
including statistics, comparisons, and log entries.
"""

from typing import List

from colorama import Fore, Style, init

from pogtool.core.interfaces import LogFormatter
from pogtool.core.models import StatsSummary, ComparisonResult, LogEntry

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class TextFormatter(LogFormatter):
    """Formatter for human-readable text output with optional colors."""
    
    def __init__(self, use_colors: bool = False) -> None:
        """
        Initialize the text formatter.
        
        Args:
            use_colors: Whether to use colored output
        """
        self.use_colors = use_colors
    
    def format_stats(self, stats: StatsSummary, show_levels: bool = True, show_patterns: bool = True, show_top: bool = True, show_time_groups: bool = True) -> str:
        """
        Format statistics summary for text output.
        
        Args:
            stats: Statistics summary to format
            show_levels: Whether to show log levels section
            show_patterns: Whether to show pattern matches section
            show_top: Whether to show top messages section
            show_time_groups: Whether to show time grouping section
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        lines.append(self._colorize("Log Statistics Summary", Fore.CYAN, bold=True))
        lines.append("=" * 50)
        lines.append("")
        
        # Basic stats
        lines.append(f"Total lines: {self._colorize(str(stats.total_lines), Fore.GREEN)}")
        lines.append("")
        
        # Log levels
        if show_levels and stats.level_counts:
            lines.append(self._colorize("Log Levels:", Fore.YELLOW, bold=True))
            for level, count in sorted(stats.level_counts.items()):
                color = self._get_level_color(level)
                lines.append(f"  {level:10}: {self._colorize(str(count), color)}")
            lines.append("")
        
        # Pattern matches
        if show_patterns and stats.pattern_counts:
            lines.append(self._colorize("Pattern Matches:", Fore.YELLOW, bold=True))
            for pattern, count in stats.pattern_counts.items():
                lines.append(f"  {pattern:20}: {self._colorize(str(count), Fore.GREEN)}")
            lines.append("")
        
        # Time grouping
        if show_time_groups and stats.time_groups:
            lines.append(self._colorize("Time Distribution:", Fore.YELLOW, bold=True))
            for time_key, count in sorted(stats.time_groups.items()):
                lines.append(f"  {time_key:20}: {self._colorize(str(count), Fore.BLUE)}")
            lines.append("")
        
        # Top messages
        if show_top and stats.top_messages:
            lines.append(self._colorize("Top Messages:", Fore.YELLOW, bold=True))
            for i, (message, count) in enumerate(stats.top_messages, 1):
                # Truncate long messages
                display_message = message[:60] + "..." if len(message) > 60 else message
                lines.append(f"  {i:2}. ({self._colorize(str(count), Fore.GREEN)}) {display_message}")
            lines.append("")
        
        return "\n".join(lines)
    
    def format_comparison(self, result: ComparisonResult) -> str:
        """
        Format comparison result for text output.
        
        Args:
            result: Comparison result to format
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        lines.append(self._colorize("Log Comparison Result", Fore.CYAN, bold=True))
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        lines.append(f"Added lines:    {self._colorize(str(len(result.added_lines)), Fore.GREEN)}")
        lines.append(f"Removed lines:  {self._colorize(str(len(result.removed_lines)), Fore.RED)}")
        lines.append(f"Modified lines: {self._colorize(str(len(result.modified_lines)), Fore.YELLOW)}")
        lines.append(f"Common lines:   {self._colorize(str(len(result.common_lines)), Fore.BLUE)}")
        lines.append(f"Total differences: {self._colorize(str(result.total_differences), Fore.MAGENTA)}")
        lines.append("")
        
        # Added lines
        if result.added_lines:
            lines.append(self._colorize("Added Lines:", Fore.GREEN, bold=True))
            for entry in result.added_lines[:20]:  # Limit output
                lines.append(f"+ {entry.raw_line}")
            if len(result.added_lines) > 20:
                lines.append(f"... and {len(result.added_lines) - 20} more added lines")
            lines.append("")
        
        # Removed lines
        if result.removed_lines:
            lines.append(self._colorize("Removed Lines:", Fore.RED, bold=True))
            for entry in result.removed_lines[:20]:  # Limit output
                lines.append(f"- {entry.raw_line}")
            if len(result.removed_lines) > 20:
                lines.append(f"... and {len(result.removed_lines) - 20} more removed lines")
            lines.append("")
        
        # Modified lines
        if result.modified_lines:
            lines.append(self._colorize("Modified Lines:", Fore.YELLOW, bold=True))
            for old_entry, new_entry in result.modified_lines[:10]:  # Limit output
                lines.append(f"- {old_entry.raw_line}")
                lines.append(f"+ {new_entry.raw_line}")
                lines.append("")
        
        return "\n".join(lines)
    
    def format_entries(self, entries: List[LogEntry]) -> str:
        """
        Format log entries for text output.
        
        Args:
            entries: Log entries to format
            
        Returns:
            Formatted text string
        """
        lines = []
        
        for entry in entries:
            # Format with timestamp and level if available
            parts = []
            
            if entry.timestamp:
                parts.append(entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            
            if entry.level:
                level_str = entry.level.name
                color = self._get_level_color(level_str)
                parts.append(self._colorize(f"[{level_str}]", color))
            
            if entry.source_file:
                parts.append(f"({entry.source_file})")
            
            parts.append(entry.message or entry.raw_line)
            
            lines.append(" ".join(parts))
        
        return "\n".join(lines)
    
    def _colorize(self, text: str, color: str, bold: bool = False) -> str:
        """
        Apply color to text if colors are enabled.
        
        Args:
            text: Text to colorize
            color: Color to apply
            bold: Whether to make text bold
            
        Returns:
            Colored or plain text
        """
        if not self.use_colors:
            return text
        
        result = color + text
        if bold:
            result = Style.BRIGHT + result
        result += Style.RESET_ALL
        return result
    
    def _get_level_color(self, level: str) -> str:
        """
        Get appropriate color for log level.
        
        Args:
            level: Log level name
            
        Returns:
            Color code
        """
        level_colors = {
            'ERROR': Fore.RED,
            'FATAL': Fore.RED,
            'CRITICAL': Fore.RED,
            'WARN': Fore.YELLOW,
            'WARNING': Fore.YELLOW,
            'INFO': Fore.GREEN,
            'DEBUG': Fore.BLUE,
            'TRACE': Fore.CYAN,
        }
        return level_colors.get(level.upper(), Fore.WHITE)