"""
Core domain models for pogtool.

This module defines the fundamental data structures and value objects
used throughout the application for representing log entries and related concepts.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class LogLevel(Enum):
    """Standard log levels with numeric priorities."""
    
    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    WARNING = 30  # Alias for WARN
    ERROR = 40
    FATAL = 50
    CRITICAL = 50  # Alias for FATAL
    
    @classmethod
    def from_string(cls, level_str: str) -> Optional["LogLevel"]:
        """Parse log level from string, case-insensitive."""
        try:
            return cls[level_str.upper()]
        except KeyError:
            # Try common variations
            variations = {
                "WARN": cls.WARNING,
                "WARNING": cls.WARNING,
                "ERR": cls.ERROR,
                "CRIT": cls.CRITICAL,
                "CRITICAL": cls.CRITICAL,
            }
            return variations.get(level_str.upper())


class TimeInterval(Enum):
    """Time grouping intervals for statistics."""
    
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass(frozen=True)
class LogEntry:
    """
    Represents a single log entry with parsed components.
    
    This is the core domain object that encapsulates all information
    about a log line, including metadata and parsed content.
    """
    
    raw_line: str
    timestamp: Optional[datetime] = None
    level: Optional[LogLevel] = None
    message: str = ""
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    extra_fields: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Initialize extra_fields as empty dict if None."""
        if self.extra_fields is None:
            object.__setattr__(self, "extra_fields", {})
    
    @property
    def normalized_message(self) -> str:
        """Get message with timestamp and level removed for comparison."""
        if not self.message:
            return self.raw_line.strip()
        return self.message.strip()
    
    @property
    def time_group(self) -> str:
        """Get a time grouping key for this entry's timestamp."""
        if not self.timestamp:
            return "unknown"
        return self.timestamp.strftime("%Y-%m-%d %H:%M")
    
    def get_time_group(self, interval: TimeInterval) -> str:
        """Get time grouping key for specified interval."""
        if not self.timestamp:
            return "unknown"
            
        if interval == TimeInterval.MINUTE:
            return self.timestamp.strftime("%Y-%m-%d %H:%M")
        elif interval == TimeInterval.HOUR:
            return self.timestamp.strftime("%Y-%m-%d %H:00")
        elif interval == TimeInterval.DAY:
            return self.timestamp.strftime("%Y-%m-%d")
        else:
            return "unknown"
    
    def matches_level(self, level_filter: str) -> bool:
        """Check if this entry matches the given level filter."""
        if not self.level:
            return level_filter.upper() in self.raw_line.upper()
        return self.level.name.upper() == level_filter.upper()
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if this entry matches the given pattern (substring match)."""
        return pattern.lower() in self.raw_line.lower()


@dataclass
class ComparisonResult:
    """Result of comparing two log entries or files."""
    
    added_lines: list[LogEntry]
    removed_lines: list[LogEntry]
    modified_lines: list[tuple[LogEntry, LogEntry]]  # (old, new)
    common_lines: list[LogEntry]
    
    @property
    def total_differences(self) -> int:
        """Total number of differences found."""
        return len(self.added_lines) + len(self.removed_lines) + len(self.modified_lines)
    
    @property
    def has_differences(self) -> bool:
        """Whether any differences were found."""
        return self.total_differences > 0


@dataclass
class StatsSummary:
    """Summary statistics for log analysis."""
    
    total_lines: int
    level_counts: Dict[str, int]
    pattern_counts: Dict[str, int]
    time_groups: Dict[str, int]
    top_messages: list[tuple[str, int]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_lines": self.total_lines,
            "level_counts": self.level_counts,
            "pattern_counts": self.pattern_counts,
            "time_groups": self.time_groups,
            "top_messages": [{"message": msg, "count": count} for msg, count in self.top_messages],
        }