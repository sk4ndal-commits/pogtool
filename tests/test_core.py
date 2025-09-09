"""
Basic tests for pogtool core functionality.

These tests verify that the main components work correctly
and can be integrated properly.
"""

import pytest
from datetime import datetime
from io import StringIO

from pogtool.core.models import LogEntry, LogLevel, TimeInterval
from pogtool.parsers.generic import GenericLogParser
from pogtool.processors import StandardLogProcessor
from pogtool.formatters.text import TextFormatter


class TestLogEntry:
    """Test LogEntry model functionality."""
    
    def test_log_entry_creation(self):
        """Test basic LogEntry creation and properties."""
        entry = LogEntry(
            raw_line="2023-09-09 23:20:15 [INFO] Application started",
            timestamp=datetime(2023, 9, 9, 23, 20, 15),
            level=LogLevel.INFO,
            message="Application started"
        )
        
        assert entry.raw_line == "2023-09-09 23:20:15 [INFO] Application started"
        assert entry.level == LogLevel.INFO
        assert entry.message == "Application started"
        assert entry.timestamp.year == 2023
    
    def test_log_entry_matches_level(self):
        """Test log level matching."""
        entry = LogEntry(
            raw_line="2023-09-09 23:20:15 [ERROR] Connection failed",
            level=LogLevel.ERROR,
        )
        
        assert entry.matches_level("ERROR")
        assert entry.matches_level("error")
        assert not entry.matches_level("INFO")
    
    def test_log_entry_matches_pattern(self):
        """Test pattern matching."""
        entry = LogEntry(
            raw_line="2023-09-09 23:20:15 [INFO] Database connection timeout",
        )
        
        assert entry.matches_pattern("timeout")
        assert entry.matches_pattern("database")
        assert entry.matches_pattern("CONNECTION")  # Case insensitive
        assert not entry.matches_pattern("error")
    
    def test_time_grouping(self):
        """Test time grouping functionality."""
        entry = LogEntry(
            raw_line="Test line",
            timestamp=datetime(2023, 9, 9, 23, 45, 30)
        )
        
        assert entry.get_time_group(TimeInterval.MINUTE) == "2023-09-09 23:45"
        assert entry.get_time_group(TimeInterval.HOUR) == "2023-09-09 23:00"
        assert entry.get_time_group(TimeInterval.DAY) == "2023-09-09"


class TestGenericLogParser:
    """Test GenericLogParser functionality."""
    
    def test_parse_simple_log(self):
        """Test parsing a simple log line."""
        parser = GenericLogParser()
        line = "2023-09-09 23:20:15 [INFO] Application started successfully"
        
        entry = parser.parse_line(line)
        
        assert entry.raw_line == line
        assert entry.level == LogLevel.INFO
        assert entry.timestamp is not None
        assert "Application started" in entry.message
    
    def test_parse_error_log(self):
        """Test parsing an error log line."""
        parser = GenericLogParser()
        line = "2023-09-09 23:20:15 ERROR: Database connection failed"
        
        entry = parser.parse_line(line)
        
        assert entry.raw_line == line
        assert entry.level == LogLevel.ERROR
        assert "Database connection failed" in entry.message
    
    def test_parse_line_without_timestamp(self):
        """Test parsing a line without timestamp."""
        parser = GenericLogParser()
        line = "[WARN] Memory usage is high"
        
        entry = parser.parse_line(line)
        
        assert entry.raw_line == line
        assert entry.level == LogLevel.WARN
        assert entry.timestamp is None
    
    def test_can_parse_format(self):
        """Test format detection capability."""
        parser = GenericLogParser()
        sample_lines = [
            "2023-09-09 23:20:15 [INFO] Test line 1",
            "2023-09-09 23:20:16 [ERROR] Test line 2"
        ]
        
        # Generic parser should always return True
        assert parser.can_parse_format(sample_lines)


class TestStandardLogProcessor:
    """Test StandardLogProcessor functionality."""
    
    def test_filter_by_level(self):
        """Test filtering entries by log level."""
        processor = StandardLogProcessor()
        entries = [
            LogEntry("Line 1", level=LogLevel.INFO, message="Info message"),
            LogEntry("Line 2", level=LogLevel.ERROR, message="Error message"),
            LogEntry("Line 3", level=LogLevel.INFO, message="Another info"),
        ]
        
        filtered = list(processor.filter_entries(iter(entries), level="ERROR"))
        
        assert len(filtered) == 1
        assert filtered[0].level == LogLevel.ERROR
    
    def test_filter_by_pattern(self):
        """Test filtering entries by pattern."""
        processor = StandardLogProcessor()
        entries = [
            LogEntry("Database connection established", message="Database connection established"),
            LogEntry("User login successful", message="User login successful"),
            LogEntry("Database query timeout", message="Database query timeout"),
        ]
        
        filtered = list(processor.filter_entries(iter(entries), patterns=["database"]))
        
        assert len(filtered) == 2
        assert all("database" in entry.raw_line.lower() for entry in filtered)
    
    def test_compute_basic_stats(self):
        """Test basic statistics computation."""
        processor = StandardLogProcessor()
        entries = [
            LogEntry("Line 1", level=LogLevel.INFO, message="Info message"),
            LogEntry("Line 2", level=LogLevel.ERROR, message="Error message"),
            LogEntry("Line 3", level=LogLevel.INFO, message="Info message"),
        ]
        
        stats = processor.compute_stats(iter(entries))
        
        assert stats.total_lines == 3
        assert stats.level_counts["INFO"] == 2
        assert stats.level_counts["ERROR"] == 1
    
    def test_compare_entries(self):
        """Test entry comparison functionality."""
        processor = StandardLogProcessor()
        entries1 = [
            LogEntry("Line 1", message="First line"),
            LogEntry("Line 2", message="Second line"),
        ]
        entries2 = [
            LogEntry("Line 1", message="First line"),
            LogEntry("Line 3", message="Third line"),
        ]
        
        result = processor.compare_entries(entries1, entries2)
        
        assert len(result.common_lines) == 1
        assert len(result.added_lines) == 1
        assert len(result.removed_lines) == 1
        assert result.has_differences


class TestTextFormatter:
    """Test TextFormatter functionality."""
    
    def test_format_stats(self):
        """Test statistics formatting."""
        formatter = TextFormatter(use_colors=False)
        
        from pogtool.core.models import StatsSummary
        stats = StatsSummary(
            total_lines=100,
            level_counts={"INFO": 70, "ERROR": 30},
            pattern_counts={"timeout": 5},
            time_groups={"2023-09-09 23:20": 10},
            top_messages=[("Test message", 5)]
        )
        
        output = formatter.format_stats(stats)
        
        assert "Total lines: 100" in output
        assert "INFO" in output
        assert "ERROR" in output
        assert "timeout" in output
    
    def test_format_entries(self):
        """Test log entries formatting."""
        formatter = TextFormatter(use_colors=False)
        entries = [
            LogEntry(
                "2023-09-09 23:20:15 [INFO] Test message",
                timestamp=datetime(2023, 9, 9, 23, 20, 15),
                level=LogLevel.INFO,
                message="Test message"
            )
        ]
        
        output = formatter.format_entries(entries)
        
        assert "2023-09-09 23:20:15" in output
        assert "[INFO]" in output
        assert "Test message" in output


if __name__ == "__main__":
    pytest.main([__file__])