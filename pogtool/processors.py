"""
Log processors for analyzing, filtering, and manipulating log entries.

This module contains concrete implementations for processing log entries
including statistics computation, filtering, comparison, and merging.
"""

import heapq
import re
from collections import Counter, defaultdict
from difflib import unified_diff
from typing import Iterator, List, Dict, Any, Set, Tuple

from pogtool.core.interfaces import LogProcessor
from pogtool.core.models import LogEntry, StatsSummary, ComparisonResult, TimeInterval


class StandardLogProcessor(LogProcessor):
    """Standard implementation of log processing operations."""
    
    def filter_entries(self, entries: Iterator[LogEntry], **filters: Any) -> Iterator[LogEntry]:
        """
        Filter log entries based on criteria.
        
        Args:
            entries: Iterator of log entries to filter
            **filters: Filter criteria (level, patterns, etc.)
            
        Yields:
            Filtered log entries
        """
        level_filter = filters.get('level')
        patterns = filters.get('patterns', [])
        
        for entry in entries:
            # Apply level filter
            if level_filter and not entry.matches_level(level_filter):
                continue
            
            # Apply pattern filters (all patterns must match)
            if patterns:
                matches_all = True
                for pattern in patterns:
                    if not entry.matches_pattern(pattern):
                        matches_all = False
                        break
                if not matches_all:
                    continue
            
            yield entry
    
    def compute_stats(self, entries: Iterator[LogEntry], **options: Any) -> StatsSummary:
        """
        Compute statistics for log entries.
        
        Args:
            entries: Iterator of log entries to analyze
            **options: Analysis options (group_by, top_n, etc.)
            
        Returns:
            Statistics summary
        """
        # Convert to list to allow multiple passes
        entry_list = list(entries)
        
        # Basic counts
        total_lines = len(entry_list)
        level_counts: Dict[str, int] = Counter()
        pattern_counts: Dict[str, int] = Counter()
        time_groups: Dict[str, int] = Counter()
        message_counts: Counter[str] = Counter()
        
        # Extract options
        group_by = options.get('group_by')
        top_n = options.get('top_n', 10)
        patterns = options.get('patterns', [])
        
        # Process entries
        for entry in entry_list:
            # Count by level
            if entry.level:
                level_counts[entry.level.name] += 1
            else:
                # Try to extract level from raw line
                level_name = self._extract_level_from_line(entry.raw_line)
                if level_name:
                    level_counts[level_name] += 1
                else:
                    level_counts['UNKNOWN'] += 1
            
            # Count patterns
            for pattern in patterns:
                if entry.matches_pattern(pattern):
                    pattern_counts[pattern] += 1
            
            # Group by time
            if group_by and entry.timestamp:
                interval = TimeInterval(group_by) if isinstance(group_by, str) else group_by
                time_key = entry.get_time_group(interval)
                time_groups[time_key] += 1
            
            # Count messages for top N
            message_counts[entry.normalized_message] += 1
        
        # Get top N messages
        top_messages = message_counts.most_common(top_n)
        
        return StatsSummary(
            total_lines=total_lines,
            level_counts=dict(level_counts),
            pattern_counts=dict(pattern_counts),
            time_groups=dict(time_groups),
            top_messages=top_messages,
        )
    
    def compare_entries(self, entries1: List[LogEntry], entries2: List[LogEntry], **options: Any) -> ComparisonResult:
        """
        Compare two sets of log entries.
        
        Args:
            entries1: First set of entries
            entries2: Second set of entries
            **options: Comparison options (ignore_timestamps, fuzzy, etc.)
            
        Returns:
            Comparison result
        """
        ignore_timestamps = options.get('ignore_timestamps', False)
        fuzzy = options.get('fuzzy', False)
        
        # Convert entries to comparable strings
        lines1 = [self._entry_to_comparable_string(entry, ignore_timestamps, fuzzy) for entry in entries1]
        lines2 = [self._entry_to_comparable_string(entry, ignore_timestamps, fuzzy) for entry in entries2]
        
        # Create sets for comparison
        set1 = set(lines1)
        set2 = set(lines2)
        
        # Find differences
        added_indices = [i for i, line in enumerate(lines2) if line not in set1]
        removed_indices = [i for i, line in enumerate(lines1) if line not in set2]
        common_indices1 = [i for i, line in enumerate(lines1) if line in set2]
        
        added_lines = [entries2[i] for i in added_indices]
        removed_lines = [entries1[i] for i in removed_indices]
        common_lines = [entries1[i] for i in common_indices1]
        
        # For modified lines, we'll use a simple heuristic
        # In a more sophisticated implementation, we'd use proper diff algorithms
        modified_lines: List[Tuple[LogEntry, LogEntry]] = []
        
        return ComparisonResult(
            added_lines=added_lines,
            removed_lines=removed_lines,
            modified_lines=modified_lines,
            common_lines=common_lines,
        )
    
    def merge_entries(self, entry_iterators: List[Iterator[LogEntry]], **options: Any) -> Iterator[LogEntry]:
        """
        Merge multiple iterators of log entries chronologically.
        
        Args:
            entry_iterators: List of entry iterators to merge
            **options: Merge options (deduplicate, tag, etc.)
            
        Yields:
            Merged log entries in chronological order
        """
        deduplicate = options.get('deduplicate', False)
        tag_source = options.get('tag_source', False)
        
        # Convert iterators to lists for easier handling
        entry_lists = [list(it) for it in entry_iterators]
        
        # Create a priority queue for merging
        # Each item is (timestamp, list_index, entry_index, entry)
        heap: List[Tuple[Any, int, int, LogEntry]] = []
        seen_lines: Set[str] = set() if deduplicate else set()
        
        # Initialize heap with first entry from each list
        for list_idx, entries in enumerate(entry_lists):
            if entries:
                entry = entries[0]
                timestamp = entry.timestamp.timestamp() if entry.timestamp else float('inf')
                heapq.heappush(heap, (timestamp, list_idx, 0, entry))
        
        # Merge entries in chronological order
        while heap:
            timestamp, list_idx, entry_idx, entry = heapq.heappop(heap)
            
            # Check for duplicates
            if deduplicate:
                line_key = entry.normalized_message
                if line_key in seen_lines:
                    # Skip duplicate, but continue to next entry
                    next_entry_idx = entry_idx + 1
                    if next_entry_idx < len(entry_lists[list_idx]):
                        next_entry = entry_lists[list_idx][next_entry_idx]
                        next_timestamp = next_entry.timestamp.timestamp() if next_entry.timestamp else float('inf')
                        heapq.heappush(heap, (next_timestamp, list_idx, next_entry_idx, next_entry))
                    continue
                seen_lines.add(line_key)
            
            # Tag with source if requested
            if tag_source and entry.source_file:
                # Modify the entry to include source tag
                # Since LogEntry is frozen, we need to create a new one
                from dataclasses import replace
                entry = replace(entry, message=f"[{entry.source_file}] {entry.message}")
            
            yield entry
            
            # Add next entry from same list to heap
            next_entry_idx = entry_idx + 1
            if next_entry_idx < len(entry_lists[list_idx]):
                next_entry = entry_lists[list_idx][next_entry_idx]
                next_timestamp = next_entry.timestamp.timestamp() if next_entry.timestamp else float('inf')
                heapq.heappush(heap, (next_timestamp, list_idx, next_entry_idx, next_entry))
    
    def _extract_level_from_line(self, line: str) -> str:
        """Extract log level from raw line using regex patterns."""
        patterns = [
            r'\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b',
            r'\[(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]',
            r'(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL):',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return 'UNKNOWN'
    
    def _entry_to_comparable_string(self, entry: LogEntry, ignore_timestamps: bool, fuzzy: bool) -> str:
        """
        Convert log entry to string for comparison.
        
        Args:
            entry: Log entry to convert
            ignore_timestamps: Whether to ignore timestamps
            fuzzy: Whether to apply fuzzy matching (normalize whitespace)
            
        Returns:
            Comparable string representation
        """
        if ignore_timestamps:
            comparable = entry.normalized_message
        else:
            comparable = entry.raw_line
        
        if fuzzy:
            # Normalize whitespace and convert to lowercase for fuzzy matching
            comparable = ' '.join(comparable.split()).lower()
        
        return comparable