"""
Main CLI interface for pogtool.

This module defines the command-line interface using Click framework,
providing the main entry point and subcommands for stats, compare, and merge operations.
"""

from typing import Optional

import click

from pogtool import __version__


@click.group()
@click.version_option(version=__version__, prog_name="pogtool")
@click.help_option("-h", "--help")
def cli() -> None:
    """
    Pogtool: A comprehensive log analysis and manipulation tool.
    
    Analyze, compare, and merge log files with advanced filtering capabilities.
    
    Use 'pogtool COMMAND --help' for detailed information about each command.
    """
    pass


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, readable=True))
@click.option("--levels", is_flag=True, help="Count lines by severity level (INFO, WARN, ERROR, etc.)")
@click.option("-e", "--regex", "patterns", multiple=True, help="Count lines matching regex patterns")
@click.option("--group-by", type=click.Choice(["minute", "hour", "day"]), help="Group counts by time interval")
@click.option("--only", type=str, help="Only process lines containing this severity level")
@click.option("--top", type=int, help="Show top N most frequent log messages")
@click.option("--json", "output_json", is_flag=True, help="Output results in JSON format")
@click.option("--csv", "output_csv", is_flag=True, help="Output results in CSV format")
@click.option("--follow", is_flag=True, help="Live mode: update stats as log files grow")
@click.option("--normalize-timestamps", is_flag=True, help="Normalize timestamps to standard format")
@click.help_option("-h", "--help")
def stats(
    files: tuple[str, ...],
    levels: bool,
    patterns: tuple[str, ...],
    group_by: Optional[str],
    only: Optional[str],
    top: Optional[int],
    output_json: bool,
    output_csv: bool,
    follow: bool,
    normalize_timestamps: bool,
) -> None:
    """
    Analyze log files and generate statistics.
    
    Count log entries by severity, patterns, or time intervals.
    Supports live monitoring and multiple output formats.
    
    Examples:
    
        # Count log levels in a single file
        pogtool stats app.log --levels
        
        # Count specific patterns across multiple files
        pogtool stats app1.log app2.log -e "timeout" -e "failed"
        
        # Group errors by minute with JSON output
        pogtool stats app.log --group-by minute --only ERROR --json
        
        # Live monitoring with top 5 messages
        pogtool stats app.log --follow --top 5
    """
    from pogtool.commands.stats import StatsCommand
    
    command = StatsCommand()
    command.execute(
        files=files,
        levels=levels,
        patterns=patterns,
        group_by=group_by,
        only=only,
        top=top,
        output_json=output_json,
        output_csv=output_csv,
        follow=follow,
        normalize_timestamps=normalize_timestamps,
    )


@cli.command()
@click.argument("file1", type=click.Path(exists=True, readable=True))
@click.argument("file2", type=click.Path(exists=True, readable=True))
@click.option("--only", type=str, help="Only compare lines containing this severity level")
@click.option("--ignore-timestamps", is_flag=True, help="Ignore timestamps when comparing")
@click.option("--color", is_flag=True, help="Colorize diff output")
@click.option("--summary", is_flag=True, help="Show summary of differences")
@click.option("--json", "output_json", is_flag=True, help="Output differences in JSON format")
@click.option("--fuzzy", is_flag=True, help="Use fuzzy matching (ignore whitespace/reordering)")
@click.help_option("-h", "--help")
def compare(
    file1: str,
    file2: str,
    only: Optional[str],
    ignore_timestamps: bool,
    color: bool,
    summary: bool,
    output_json: bool,
    fuzzy: bool,
) -> None:
    """
    Compare two log files and show differences.
    
    Display added, removed, or modified log entries between two files.
    Supports filtering, colorized output, and various comparison modes.
    
    Examples:
    
        # Basic comparison
        pogtool compare old.log new.log
        
        # Compare only ERROR entries with colors
        pogtool compare old.log new.log --only ERROR --color
        
        # Ignore timestamps and show summary
        pogtool compare old.log new.log --ignore-timestamps --summary
        
        # Fuzzy matching with JSON output
        pogtool compare old.log new.log --fuzzy --json
    """
    from pogtool.commands.compare import CompareCommand
    
    command = CompareCommand()
    command.execute(
        file1=file1,
        file2=file2,
        only=only,
        ignore_timestamps=ignore_timestamps,
        color=color,
        summary=summary,
        output_json=output_json,
        fuzzy=fuzzy,
    )


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, readable=True))
@click.option("-o", "--output", type=click.Path(), help="Output file (default: stdout)")
@click.option("--tag", is_flag=True, help="Add filename as tag/column to each entry")
@click.option("--normalize-timestamps", is_flag=True, help="Normalize timestamps to standard format")
@click.option("--deduplicate", is_flag=True, help="Remove duplicate entries")
@click.option("--follow", is_flag=True, help="Stream mode: continuously merge growing files")
@click.option("--compressed", is_flag=True, help="Support compressed input files (.gz)")
@click.help_option("-h", "--help")
def merge(
    files: tuple[str, ...],
    output: Optional[str],
    tag: bool,
    normalize_timestamps: bool,
    deduplicate: bool,
    follow: bool,
    compressed: bool,
) -> None:
    """
    Merge multiple log files chronologically.
    
    Combine log files by timestamp while maintaining chronological order.
    Supports various timestamp formats and streaming mode.
    
    Examples:
    
        # Merge two logs to stdout
        pogtool merge app1.log app2.log
        
        # Merge with filename tags to output file
        pogtool merge *.log --tag --output merged.log
        
        # Normalize timestamps and deduplicate
        pogtool merge app1.log app2.log --normalize-timestamps --deduplicate
        
        # Stream mode for live merging
        pogtool merge app1.log app2.log --follow
    """
    from pogtool.commands.merge import MergeCommand
    
    command = MergeCommand()
    command.execute(
        files=files,
        output=output,
        tag=tag,
        normalize_timestamps=normalize_timestamps,
        deduplicate=deduplicate,
        follow=follow,
        compressed=compressed,
    )


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()