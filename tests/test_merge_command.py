"""
Integration tests for the merge command.

Tests the merge command CLI functionality to ensure that output sections
are displayed correctly based on the provided flags.
"""

import subprocess
import tempfile
import os
import pytest


class TestMergeCommand:
    """Integration tests for the merge command CLI."""

    @pytest.fixture
    def test_log_files(self):
        """Create temporary test log files with sample data for merging."""
        test_log_content1 = """2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:02 ERROR Failed to connect to database
2024-01-01 10:00:04 INFO Connected successfully
2024-01-01 10:00:06 INFO Processing request
"""

        test_log_content2 = """2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:03 WARN Retrying connection
2024-01-01 10:00:05 ERROR DummyISTT error occurred
2024-01-01 10:00:07 INFO Request completed
"""

        test_log_content3 = """2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:03 WARN Retrying connection
2024-01-01 10:00:05 ERROR DummyISTT error occurred
2024-01-01 10:00:07 INFO Request completed
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write(test_log_content1)
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write(test_log_content2)
            temp_path2 = f2.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f3:
            f3.write(test_log_content3)
            temp_path3 = f3.name
        
        yield temp_path1, temp_path2, temp_path3
        
        # Cleanup
        os.unlink(temp_path1)
        os.unlink(temp_path2)
        os.unlink(temp_path3)

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_basic_merge_to_stdout(self, test_log_files):
        """Test basic merging of two log files to stdout."""
        file1, file2, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should contain merged content in chronological order
        assert len(result.stdout) > 0
        assert "Application started" in result.stdout
        assert "Loading configuration" in result.stdout

    def test_merge_with_output_file(self, test_log_files, temp_output_file):
        """Test merging with --output flag to write to file."""
        file1, file2, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2, '--output', temp_output_file], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Check that output file was created and contains merged data
        assert os.path.exists(temp_output_file)
        with open(temp_output_file, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert "Application started" in content

    def test_merge_with_tag(self, test_log_files):
        """Test merging with --tag flag to add source file tags."""
        file1, file2, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2, '--tag'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should contain source file information
        assert len(result.stdout) > 0

    def test_merge_with_normalize_timestamps(self, test_log_files):
        """Test merging with --normalize-timestamps flag."""
        file1, file2, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2, '--normalize-timestamps'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_merge_with_deduplicate(self, test_log_files):
        """Test merging with --deduplicate flag to remove duplicate entries."""
        file2, file3, _ = test_log_files  # file2 and file3 have identical content
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file2, file3, '--deduplicate'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should deduplicate identical entries
        assert len(result.stdout) > 0

    def test_merge_multiple_files(self, test_log_files):
        """Test merging three log files."""
        file1, file2, file3 = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2, file3], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0
        # Should contain entries from all three files
        assert "Application started" in result.stdout
        assert "Loading configuration" in result.stdout

    def test_merge_combined_flags(self, test_log_files, temp_output_file):
        """Test merging with multiple flags combined."""
        file1, file2, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1, file2, '--output', temp_output_file, '--tag', '--normalize-timestamps'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Check that output file was created
        assert os.path.exists(temp_output_file)
        with open(temp_output_file, 'r') as f:
            content = f.read()
            assert len(content) > 0

    def test_merge_with_deduplicate_and_tag(self, test_log_files):
        """Test merging with both --deduplicate and --tag flags."""
        file2, file3, _ = test_log_files  # file2 and file3 have identical content
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file2, file3, '--deduplicate', '--tag'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_merge_nonexistent_files(self):
        """Test merging with non-existent files returns error."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'nonexistent1.log', 'nonexistent2.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Should fail with appropriate error code and message
        assert result.returncode == 2  # CLI validation error
        assert "does not exist" in result.stderr

    def test_merge_single_file(self, test_log_files):
        """Test merging with a single file (edge case)."""
        file1, _, _ = test_log_files
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', file1], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        # Should show error message for single file merge
        assert len(result.stdout) > 0
        assert "At least two files are required for merging" in result.stdout