"""
Integration tests for the compare command.

Tests the compare command CLI functionality to ensure that output sections
are displayed correctly based on the provided flags.
"""

import subprocess
import tempfile
import os
import pytest


class TestCompareCommand:
    """Integration tests for the compare command CLI."""

    @pytest.fixture
    def test_log_files(self):
        """Create temporary test log files with sample data for comparison."""
        test_log_content1 = """2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:02 ERROR Failed to connect to database
2024-01-01 10:00:03 WARN Retrying connection
2024-01-01 10:00:04 INFO Connected successfully
2024-01-01 10:00:05 ERROR DummyISTT error occurred
2024-01-01 10:00:06 INFO Processing request
"""

        test_log_content2 = """2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:02 ERROR Failed to connect to database
2024-01-01 10:00:03 WARN Retrying connection
2024-01-01 10:00:04 INFO Connected successfully
2024-01-01 10:00:05 ERROR Different error occurred
2024-01-01 10:00:06 INFO Processing request
2024-01-01 10:00:07 INFO New log entry
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write(test_log_content1)
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write(test_log_content2)
            temp_path2 = f2.name
        
        yield temp_path1, temp_path2
        
        # Cleanup
        os.unlink(temp_path1)
        os.unlink(temp_path2)

    def test_basic_compare(self, test_log_files):
        """Test basic comparison between two log files."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should show differences between the files
        assert len(result.stdout) > 0

    def test_compare_with_only_filter(self, test_log_files):
        """Test comparison with --only flag to filter by log level."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--only', 'ERROR'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should show differences only in ERROR lines
        assert len(result.stdout) > 0

    def test_compare_ignore_timestamps(self, test_log_files):
        """Test comparison with --ignore-timestamps flag."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--ignore-timestamps'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_compare_with_color(self, test_log_files):
        """Test comparison with --color flag."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--color'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_compare_with_summary(self, test_log_files):
        """Test comparison with --summary flag."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--summary'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Comparison Summary:" in result.stdout
        assert "Added lines:" in result.stdout
        assert "Removed lines:" in result.stdout
        assert "Modified lines:" in result.stdout
        assert "Common lines:" in result.stdout

    def test_compare_with_json_output(self, test_log_files):
        """Test comparison with --json flag for JSON output."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--json'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should produce JSON output (basic check for structure)
        assert len(result.stdout) > 0

    def test_compare_with_fuzzy_matching(self, test_log_files):
        """Test comparison with --fuzzy flag for fuzzy matching."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--fuzzy'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_compare_combined_flags(self, test_log_files):
        """Test comparison with multiple flags combined."""
        file1, file2 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', file1, file2, '--only', 'ERROR', '--summary'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Comparison Summary:" in result.stdout

    def test_compare_nonexistent_files(self):
        """Test comparison with non-existent files returns error."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'nonexistent1.log', 'nonexistent2.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Should fail with appropriate error code and message
        assert result.returncode == 2  # CLI validation error
        assert "does not exist" in result.stderr