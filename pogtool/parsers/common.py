"""
Common log format parser for Apache/Nginx style logs.

This parser handles the Common Log Format (CLF) and Combined Log Format
used by web servers like Apache and Nginx.
"""

import re
from datetime import datetime
from typing import List, Optional

from pogtool.core.interfaces import LogParser
from pogtool.core.models import LogEntry, LogLevel


class CommonLogParser(LogParser):
    """
    Parser for Common Log Format and Combined Log Format.
    
    Handles standard web server log formats:
    - Common Log Format: host ident authuser [timestamp] "request" status size
    - Combined Log Format: CLF + "referer" "user-agent"
    """
    
    # Common Log Format regex
    CLF_PATTERN = re.compile(
        r'^(\S+) (\S+) (\S+) \[([^\]]+)\] "([^"]*)" (\d{3}) (\S+)(?: "([^"]*)" "([^"]*)")?'
    )
    
    def __init__(self) -> None:
        """Initialize the common log parser."""
        pass
    
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
        
        match = self.CLF_PATTERN.match(line)
        if not match:
            # Fall back to treating entire line as message
            return LogEntry(
                raw_line=line,
                message=line.strip(),
                source_file=source_file,
                line_number=line_number,
            )
        
        # Extract components
        host = match.group(1)
        ident = match.group(2) 
        authuser = match.group(3)
        timestamp_str = match.group(4)
        request = match.group(5)
        status_code = int(match.group(6))
        size = match.group(7)
        referer = match.group(8) if match.group(8) else None
        user_agent = match.group(9) if match.group(9) else None
        
        # Parse timestamp
        timestamp = self._parse_timestamp(timestamp_str)
        
        # Determine log level based on status code
        level = self._status_to_level(status_code)
        
        # Build message
        message = f"{request} -> {status_code} {size}"
        
        # Extra fields for web log specific data
        extra_fields = {
            'host': host,
            'ident': ident,
            'authuser': authuser,
            'request': request,
            'status_code': status_code,
            'size': size,
        }
        
        if referer:
            extra_fields['referer'] = referer
        if user_agent:
            extra_fields['user_agent'] = user_agent
        
        return LogEntry(
            raw_line=line,
            timestamp=timestamp,
            level=level,
            message=message,
            source_file=source_file,
            line_number=line_number,
            extra_fields=extra_fields,
        )
    
    def can_parse_format(self, sample_lines: List[str]) -> bool:
        """
        Determine if this parser can handle the given log format.
        
        Args:
            sample_lines: Sample lines to analyze
            
        Returns:
            True if lines look like Common Log Format
        """
        if not sample_lines:
            return False
            
        # Check if at least 70% of sample lines match CLF pattern
        matches = sum(1 for line in sample_lines[:10] if self.CLF_PATTERN.match(line.strip()))
        return matches >= len(sample_lines[:10]) * 0.7
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse Apache/Nginx timestamp format.
        
        Format: 09/Sep/2023:23:20:15 +0000
        """
        try:
            # Remove timezone offset for simplicity
            if '+' in timestamp_str or '-' in timestamp_str[-5:]:
                timestamp_str = timestamp_str.rsplit(None, 1)[0]
            
            return datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S')
        except ValueError:
            return None
    
    def _status_to_level(self, status_code: int) -> Optional[LogLevel]:
        """
        Convert HTTP status code to log level.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Appropriate log level
        """
        if status_code < 300:
            return LogLevel.INFO
        elif status_code < 400:
            return LogLevel.INFO  # Redirects are informational
        elif status_code < 500:
            return LogLevel.WARN  # Client errors are warnings
        else:
            return LogLevel.ERROR  # Server errors