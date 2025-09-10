"""
Integration tests for the compare command.

Tests the compare command CLI functionality with actual usage scenarios
to ensure output content and structure are correct, similar to user examples.
"""

import subprocess
import tempfile
import os
import json
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

    def test_compare_actual_usage_basic_output_structure(self):
        """Test actual usage: validate basic output structure and content."""
        # Use real test log files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'testlogs/app1.log', 'testlogs/app2.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Validate output structure
        assert "Log Comparison Result" in output
        assert "Added lines:" in output
        assert "Removed lines:" in output
        assert "Modified lines:" in output
        assert "Common lines:" in output
        assert "Total differences:" in output
        assert "Added Lines:" in output
        assert "Removed Lines:" in output
        
        # Validate actual content from the files
        assert "WebServer] Server starting on port 8080" in output
        assert "EmailService] Email service initialized" in output

    def test_compare_actual_usage_json_output(self):
        """Test actual usage: validate JSON output structure and content."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'testlogs/app1.log', 'testlogs/app2.log', '--json'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        
        # Parse and validate JSON structure
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
        
        # Validate JSON structure
        assert "summary" in data
        assert "details" in data
        assert "added_lines" in data["summary"]
        assert "removed_lines" in data["summary"]
        assert "modified_lines" in data["summary"]
        assert "common_lines" in data["summary"]
        assert "total_differences" in data["summary"]
        assert "has_differences" in data["summary"]
        
        # Validate details section
        assert "added_lines" in data["details"]
        assert "removed_lines" in data["details"]
        assert "modified_lines" in data["details"]
        assert "common_lines" in data["details"]
        
        # Validate actual counts match between files
        assert data["summary"]["added_lines"] > 0
        assert data["summary"]["removed_lines"] > 0
        assert data["summary"]["has_differences"] is True

    def test_compare_actual_usage_only_filter(self):
        """Test actual usage: validate --only filter works correctly."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'testlogs/app1.log', 'testlogs/app2.log', '--only', 'ERROR'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should only show ERROR level differences
        assert "ERROR" in output
        # Should not contain other levels when filtering
        lines = output.split('\n')
        log_lines = [line for line in lines if line.startswith('+') or line.startswith('-')]
        for line in log_lines:
            # Every actual log line should contain ERROR when filtered
            if any(keyword in line for keyword in ['WebServer', 'Database', 'Auth', 'EmailService', 'FileManager', 'Security']):
                assert "ERROR" in line

    def test_compare_actual_usage_summary_only(self):
        """Test actual usage: validate --summary flag shows only summary."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'testlogs/app1.log', 'testlogs/app2.log', '--summary'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should show summary
        assert "Comparison Summary:" in output
        assert "Added lines:" in output
        assert "Removed lines:" in output
        assert "Modified lines:" in output
        assert "Common lines:" in output
        assert "Total differences:" in output
        
        # Should NOT show detailed line-by-line comparison
        assert "Added Lines:" not in output
        assert "Removed Lines:" not in output
        assert "WebServer] Server starting" not in output

    def test_compare_actual_usage_identical_files(self):
        """Test actual usage: validate behavior with identical files."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'compare', 'testlogs/app1.log', 'testlogs/app1.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should show no differences
        assert "Added lines:    0" in output
        assert "Removed lines:  0" in output
        assert "Modified lines: 0" in output
        assert "Total differences: 0" in output
        
        # Should not have Added Lines or Removed Lines sections
        assert "Added Lines:" not in output
        assert "Removed Lines:" not in output

    def test_compare_actual_usage_ignore_timestamps(self):
        """Test actual usage: validate --ignore-timestamps works correctly."""
        # Create two files with same content but different timestamps
        content1 = """2024-01-01 10:00:01 INFO Test message
2024-01-01 10:00:02 ERROR Test error"""
        
        content2 = """2024-12-25 15:30:45 INFO Test message
2024-12-25 15:30:46 ERROR Test error"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write(content1)
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write(content2)
            temp_path2 = f2.name
        
        try:
            # Without ignore-timestamps should show differences
            result_with_timestamps = subprocess.run(
                ['python3', 'pogtool.py', 'compare', temp_path1, temp_path2], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # With ignore-timestamps should show no differences
            result_ignore_timestamps = subprocess.run(
                ['python3', 'pogtool.py', 'compare', temp_path1, temp_path2, '--ignore-timestamps'], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # With timestamps, should show differences
            assert "Total differences: 4" in result_with_timestamps.stdout
            
            # Without timestamps, should show no differences (or fewer)
            assert "Total differences: 0" in result_ignore_timestamps.stdout
            
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)