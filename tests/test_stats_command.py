"""
Integration tests for the stats command.

Tests the stats command CLI functionality to ensure that output sections
are displayed correctly based on the provided flags.
"""

import subprocess
import tempfile
import os
import pytest


class TestStatsCommand:
    """Integration tests for the stats command CLI."""

    @pytest.fixture
    def test_log_file(self):
        """Create a temporary test log file with sample data."""
        test_log_content = """2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:02 ERROR Failed to connect to database
2024-01-01 10:00:03 WARN Retrying connection
2024-01-01 10:00:04 INFO Connected successfully
2024-01-01 10:00:05 ERROR DummyISTT error occurred
2024-01-01 10:00:06 INFO Processing request
2024-01-01 10:00:07 DEBUG DummyISTT debug message
2024-01-01 10:00:08 WARN Low memory warning
2024-01-01 10:00:09 ERROR Another error
2024-01-01 10:00:10 INFO DummyISTT info message
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(test_log_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)

    def test_pattern_only_shows_pattern_matches(self, test_log_file):
        """Test that using only -e flag shows only Pattern Matches section."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'stats', test_log_file, '-e', 'DummyISTT'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Pattern Matches:" in result.stdout
        assert "Log Levels:" not in result.stdout
        assert "Top Messages:" not in result.stdout
        assert "DummyISTT           : 3" in result.stdout

    def test_levels_only_shows_log_levels(self, test_log_file):
        """Test that using only --levels flag shows only Log Levels section."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'stats', test_log_file, '--levels'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Log Levels:" in result.stdout
        assert "Pattern Matches:" not in result.stdout
        assert "Top Messages:" not in result.stdout
        assert "ERROR" in result.stdout
        assert "INFO" in result.stdout

    def test_top_only_shows_top_messages(self, test_log_file):
        """Test that using only --top flag shows only Top Messages section."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'stats', test_log_file, '--top', '5'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Top Messages:" in result.stdout
        assert "Log Levels:" not in result.stdout
        assert "Pattern Matches:" not in result.stdout

    def test_combination_shows_multiple_sections(self, test_log_file):
        """Test that combining flags shows multiple sections."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'stats', test_log_file, '--levels', '-e', 'DummyISTT'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Log Levels:" in result.stdout
        assert "Pattern Matches:" in result.stdout
        assert "Top Messages:" not in result.stdout

    def test_no_flags_shows_all_sections(self, test_log_file):
        """Test backward compatibility: no flags should show all sections."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'stats', test_log_file], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Log Levels:" in result.stdout
        assert "Top Messages:" in result.stdout
        # Pattern Matches only shown if patterns are provided, so not expected here