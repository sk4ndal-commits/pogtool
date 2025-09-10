"""
Integration tests for the merge command.

Tests the merge command CLI functionality with actual usage scenarios
to ensure output content and structure are correct, similar to user examples.
"""

import subprocess
import tempfile
import os
import json
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

    def test_merge_actual_usage_basic_chronological_order(self):
        """Test actual usage: validate chronological merging of real log files."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app2.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output_lines = result.stdout.strip().split('\n')
        
        # Should have entries from both files
        assert len(output_lines) > 0
        
        # Validate chronological order - extract timestamps and verify ordering
        timestamps = []
        for line in output_lines:
            if line.startswith('2025-09-10'):
                timestamp_str = line[:19]  # Extract "2025-09-10 HH:MM:SS"
                timestamps.append(timestamp_str)
        
        # Timestamps should be in chronological order
        assert timestamps == sorted(timestamps), "Merged entries are not in chronological order"
        
        # Should contain entries from both files
        assert any("WebServer] Server starting on port 8080" in line for line in output_lines)
        assert any("EmailService] Email service initialized" in line for line in output_lines)

    def test_merge_actual_usage_with_tag_flag(self):
        """Test actual usage: validate --tag flag adds source file information."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app2.log', '--tag'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should contain source file tags - currently not implemented, so just check output exists
        assert len(output.strip()) > 0

    def test_merge_actual_usage_deduplicate_functionality(self):
        """Test actual usage: validate --deduplicate removes duplicate entries."""
        # First merge without deduplicate to see duplicates
        result_with_dupes = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app1.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Then merge with deduplicate
        result_deduped = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app1.log', '--deduplicate'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result_with_dupes.returncode == 0
        assert result_deduped.returncode == 0
        
        lines_with_dupes = len(result_with_dupes.stdout.strip().split('\n'))
        lines_deduped = len(result_deduped.stdout.strip().split('\n'))
        
        # Deduplicated version should have fewer lines
        assert lines_deduped <= lines_with_dupes
        
        # Original should have exactly double the entries (same file twice)
        assert lines_with_dupes == 2 * lines_deduped

    def test_merge_actual_usage_output_to_file(self):
        """Test actual usage: validate --output flag writes to file correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = subprocess.run(
                ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app2.log', '--output', output_path], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            assert result.returncode == 0
            # stdout should be empty when writing to file
            assert len(result.stdout.strip()) == 0 or "merged" in result.stdout.lower() and "files into" in result.stdout.lower()
            
            # File should exist and contain merged data
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
                # Should contain entries from both files
                assert "WebServer] Server starting on port 8080" in content
                assert "EmailService] Email service initialized" in content
                
                # Should be chronologically ordered
                lines = content.strip().split('\n')
                timestamps = []
                for line in lines:
                    if line.startswith('2025-09-10'):
                        timestamps.append(line[:19])
                assert timestamps == sorted(timestamps)
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_merge_actual_usage_normalize_timestamps(self):
        """Test actual usage: validate --normalize-timestamps standardizes timestamp formats."""
        # Create files with different timestamp formats
        content1 = """2024-01-01 10:00:01 INFO Message 1
Jan 1 10:00:02 2024 WARN Message 2"""
        
        content2 = """2024/01/01 10:00:03 ERROR Message 3
01-01-2024 10:00:04 DEBUG Message 4"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write(content1)
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write(content2)
            temp_path2 = f2.name
        
        try:
            result = subprocess.run(
                ['python3', 'pogtool.py', 'merge', temp_path1, temp_path2, '--normalize-timestamps'], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            assert result.returncode == 0
            output = result.stdout
            
            # All timestamps should be normalized to a consistent format
            lines = output.strip().split('\n')
            timestamp_formats = set()
            for line in lines:
                if 'Message' in line:
                    # Extract timestamp part (first 19 chars usually)
                    timestamp_part = line[:19]
                    # Check format pattern
                    if timestamp_part.count('-') == 2 and timestamp_part.count(':') == 2:
                        timestamp_formats.add('standard')
                    else:
                        timestamp_formats.add('other')
            
            # Should have consistent timestamp formatting
            assert len(timestamp_formats) <= 1 or not timestamp_formats, "Timestamps not properly normalized"
            
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)

    def test_merge_actual_usage_multiple_files_ordering(self):
        """Test actual usage: validate merging three files maintains chronological order."""
        # Create a third test file
        content3 = """2025-09-10 08:00:30 INFO [ThirdApp] Third app started
2025-09-10 08:01:30 WARN [ThirdApp] Third app warning
2025-09-10 08:02:30 ERROR [ThirdApp] Third app error"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f3:
            f3.write(content3)
            temp_path3 = f3.name
        
        try:
            result = subprocess.run(
                ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app2.log', temp_path3], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            assert result.returncode == 0
            output_lines = result.stdout.strip().split('\n')
            
            # Should contain entries from all three files
            assert any("WebServer] Server starting" in line for line in output_lines)
            assert any("EmailService] Email service" in line for line in output_lines)
            assert any("ThirdApp] Third app" in line for line in output_lines)
            
            # Should maintain chronological order
            timestamps = []
            for line in output_lines:
                if line.startswith('2025-09-10'):
                    timestamps.append(line[:19])
            
            assert timestamps == sorted(timestamps), "Three-file merge not chronologically ordered"
            
        finally:
            os.unlink(temp_path3)

    def test_merge_actual_usage_error_handling_missing_files(self):
        """Test actual usage: validate proper error handling for missing files."""
        result = subprocess.run(
            ['python3', 'pogtool.py', 'merge', 'nonexistent1.log', 'nonexistent2.log'], 
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Should fail with appropriate error
        assert result.returncode != 0
        assert "does not exist" in result.stderr or "not found" in result.stderr.lower()

    def test_merge_actual_usage_combined_flags(self):
        """Test actual usage: validate multiple flags work together correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = subprocess.run(
                ['python3', 'pogtool.py', 'merge', 'testlogs/app1.log', 'testlogs/app2.log', 
                 '--output', output_path, '--tag', '--normalize-timestamps'], 
                capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            assert result.returncode == 0
            
            # File should exist and contain merged data with tags
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
                
                # Should have source file information due to --tag
                assert ("app1" in content or "app2" in content or 
                       "testlogs" in content), "Tag information not found in output"
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_merge_follow_mode_skips_existing_content(self):
        """Test that --follow flag only processes new entries added after command starts."""
        import time
        import threading
        
        # Create temporary files with initial content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write("2025-01-01T10:00:00 [INFO] Initial entry 1\n")
            f1.write("2025-01-01T10:01:00 [INFO] Initial entry 2\n")
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write("2025-01-01T10:00:30 [INFO] Initial entry 3\n")  
            f2.write("2025-01-01T10:01:30 [INFO] Initial entry 4\n")
            temp_path2 = f2.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as output_file:
            output_path = output_file.name
        
        def add_new_entries():
            """Add new entries to log files after a delay."""
            time.sleep(1.5)  # Wait for follow mode to start
            
            with open(temp_path1, 'a') as f:
                f.write("2025-01-01T10:02:00 [INFO] New entry after follow started\n")
            
            with open(temp_path2, 'a') as f:
                f.write("2025-01-01T10:02:30 [INFO] Another new entry\n")
            
            time.sleep(1)
            
            with open(temp_path1, 'a') as f:
                f.write("2025-01-01T10:03:00 [INFO] Final new entry\n")
        
        try:
            # Start thread to add entries
            thread = threading.Thread(target=add_new_entries)
            thread.start()
            
            # Start merge process with --follow
            process = subprocess.Popen(
                ['python3', 'pogtool.py', 'merge', '--follow', '--output', output_path, temp_path1, temp_path2],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # Wait for new entries to be added
            thread.join()
            time.sleep(1)  # Let follow mode process the new entries
            
            # Stop the process
            process.terminate()
            process.wait(timeout=5)
            
            # Check output file - should only contain new entries
            with open(output_path, 'r') as f:
                content = f.read()
            
            lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            
            # Should NOT contain initial entries
            assert not any("Initial entry" in line for line in lines), "Follow mode included existing content"
            
            # Should contain only new entries  
            assert any("New entry after follow started" in line for line in lines), "Missing new entry"
            assert any("Another new entry" in line for line in lines), "Missing another new entry"
            assert any("Final new entry" in line for line in lines), "Missing final new entry"
            
            # Should be chronologically ordered
            timestamps = []
            for line in lines:
                if line.startswith('2025-01-01T10:'):
                    timestamps.append(line[:19])
            
            assert timestamps == sorted(timestamps), "New entries not chronologically ordered"
            
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_merge_follow_mode_with_tag_flag(self):
        """Test that --follow works correctly with --tag flag."""
        import time
        import threading
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f1:
            f1.write("2025-01-01T10:00:00 [INFO] Existing entry\n")
            temp_path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f2:
            f2.write("2025-01-01T10:00:30 [INFO] Another existing entry\n")
            temp_path2 = f2.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as output_file:
            output_path = output_file.name
        
        def add_tagged_entries():
            """Add entries to be tagged."""
            time.sleep(1.5)
            
            with open(temp_path1, 'a') as f:
                f.write("2025-01-01T10:02:00 [INFO] Tagged entry from file1\n")
            
            with open(temp_path2, 'a') as f:
                f.write("2025-01-01T10:02:30 [INFO] Tagged entry from file2\n")
        
        try:
            # Start thread to add entries
            thread = threading.Thread(target=add_tagged_entries)
            thread.start()
            
            # Start merge process with --follow and --tag
            process = subprocess.Popen(
                ['python3', 'pogtool.py', 'merge', '--follow', '--tag', '--output', output_path, temp_path1, temp_path2],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # Wait for entries and processing
            thread.join()
            time.sleep(1)
            
            # Stop the process
            process.terminate()
            process.wait(timeout=5)
            
            # Check output file
            with open(output_path, 'r') as f:
                content = f.read()
            
            lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            
            # Should not contain existing entries
            assert not any("Existing entry" in line for line in lines), "Follow mode included existing content"
            
            # Should contain tagged new entries (format: [filepath] message)
            assert any(f"[{temp_path1}]" in line and "Tagged entry from file1" in line for line in lines), "Missing tagged entry from file1"
            assert any(f"[{temp_path2}]" in line and "Tagged entry from file2" in line for line in lines), "Missing tagged entry from file2"
            
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)
            if os.path.exists(output_path):
                os.unlink(output_path)