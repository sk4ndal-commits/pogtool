"""
Generic log parser that handles common log formats.

This parser uses regular expressions to extract timestamps, log levels,
and messages from various log formats.
"""

import re
from datetime import datetime
from typing import List, Optional

from dateutil.parser import parse as parse_date

from pogtool.core.interfaces import LogParser
from pogtool.core.models import LogEntry, LogLevel


class GenericLogParser(LogParser):
    """
    Generic log parser that can handle most common log formats.
    
    Supports various timestamp formats, log levels, and message extraction.
    Falls back to treating the entire line as message if parsing fails.
    """
    
    # Common timestamp patterns
    TIMESTAMP_PATTERNS = [
        # ISO format: 2023-09-09T23:20:15.123Z
        r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)',
        # Common log format: 2023-09-09 23:20:15
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        # Apache format: 09/Sep/2023:23:20:15 +0000
        r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})',
        # Syslog format: Sep  9 23:20:15
        r'(\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2})',
        # Simple time: 23:20:15
        r'(\d{2}:\d{2}:\d{2})',
    ]
    
    # Log level patterns (case insensitive)
    LEVEL_PATTERNS = [
        r'\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b',
        r'\[(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]',
        r'(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL):',
    ]
    
    def __init__(self) -> None:
        """Initialize the generic parser with compiled regex patterns."""
        self._timestamp_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.TIMESTAMP_PATTERNS]
        self._level_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.LEVEL_PATTERNS]
    
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
        line = line.rstrip('\n\r')
        
        # Extract timestamp
        timestamp = self._extract_timestamp(line)
        
        # Extract log level
        level = self._extract_level(line)
        
        # Extract message (remove timestamp and level if found)
        message = self._extract_message(line, timestamp, level)
        
        return LogEntry(
            raw_line=line,
            timestamp=timestamp,
            level=level,
            message=message,
            source_file=source_file,
            line_number=line_number,
        )
    
    def can_parse_format(self, sample_lines: List[str]) -> bool:
        """
        Determine if this parser can handle the given log format.
        
        Args:
            sample_lines: Sample lines to analyze
            
        Returns:
            True if this parser can handle the format (always True for generic parser)
        """
        # Generic parser can attempt to parse any format
        return True
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line."""
        for regex in self._timestamp_regexes:
            match = regex.search(line)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Use dateutil parser for flexible timestamp parsing
                    return parse_date(timestamp_str, fuzzy=True)
                except (ValueError, TypeError):
                    # If dateutil fails, try some common formats manually
                    try:
                        # Try common formats
                        formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%d/%b/%Y:%H:%M:%S %z',
                            '%b %d %H:%M:%S',
                            '%H:%M:%S',
                        ]
                        for fmt in formats:
                            try:
                                return datetime.strptime(timestamp_str, fmt)
                            except ValueError:
                                continue
                    except (ValueError, TypeError):
                        pass
        return None
    
    def _extract_level(self, line: str) -> Optional[LogLevel]:
        """Extract log level from log line."""
        for regex in self._level_regexes:
            match = regex.search(line)
            if match:
                level_str = match.group(1)
                return LogLevel.from_string(level_str)
        return None
    
    def _extract_message(self, line: str, timestamp: Optional[datetime], level: Optional[LogLevel]) -> str:
        """
        Extract the message part of the log line.
        
        Removes timestamp and level information to get the core message.
        """
        message = line
        
        # Remove timestamp if found
        for regex in self._timestamp_regexes:
            message = regex.sub('', message, count=1)
        
        # Remove level if found
        if level:
            for regex in self._level_regexes:
                message = regex.sub('', message, count=1)
        
        # Clean up whitespace and common separators
        message = message.strip(' \t-:[]')
        
        # If message is empty or too short, use original line
        if not message or len(message) < 3:
            return line.strip()
        
        return message