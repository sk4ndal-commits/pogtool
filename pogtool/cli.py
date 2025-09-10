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


@cli.command(epilog="""Examples:

  pogtool stats app.log --levels
    → Count log levels in a single file

  pogtool stats app1.log app2.log -e "timeout" -e "failed"
    → Count specific patterns across multiple files

  pogtool stats app.log --group-by minute --only ERROR --json
    → Group errors by minute with JSON output

  pogtool stats app.log --follow --top 5
    → Live monitoring with top 5 messages
""")
@click.argument("files", nargs=-1, type=click.Path(exists=True, readable=True))
@click.option("-l", "--levels", is_flag=True, help="Count lines by severity level (INFO, WARN, ERROR, etc.)")
@click.option("-e", "--regex", "patterns", multiple=True, help="Count lines matching regex patterns")
@click.option("-g", "--group-by", type=click.Choice(["minute", "hour", "day"]), help="Group counts by time interval")
@click.option("-O", "--only", type=str, help="Only process lines containing this severity level")
@click.option("-t", "--top", type=int, help="Show top N most frequent log messages")
@click.option("-j", "--json", "output_json", is_flag=True, help="Output results in JSON format")
@click.option("-c", "--csv", "output_csv", is_flag=True, help="Output results in CSV format")
@click.option("-f", "--follow", is_flag=True, help="Live mode: update stats as log files grow")
@click.option("-n", "--normalize-timestamps", is_flag=True, help="Normalize timestamps to standard format")
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

    Count log entries by severity, patterns, or time intervals. Supports live
    monitoring and multiple output formats.
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


@cli.command(epilog="""Examples:

  pogtool compare old.log new.log
    → Basic comparison

  pogtool compare old.log new.log --only ERROR --color
    → Compare only ERROR entries with colors

  pogtool compare old.log new.log --ignore-timestamps --summary
    → Ignore timestamps and show summary

  pogtool compare old.log new.log --fuzzy --json
    → Fuzzy matching with JSON output
""")
@click.argument("file1", type=click.Path(exists=True, readable=True))
@click.argument("file2", type=click.Path(exists=True, readable=True))
@click.option("-O", "--only", type=str, help="Only compare lines containing this severity level")
@click.option("-i", "--ignore-timestamps", is_flag=True, help="Ignore timestamps when comparing")
@click.option("-c", "--color", is_flag=True, help="Colorize diff output")
@click.option("-s", "--summary", is_flag=True, help="Show summary of differences")
@click.option("-j", "--json", "output_json", is_flag=True, help="Output differences in JSON format")
@click.option("-z", "--fuzzy", is_flag=True, help="Use fuzzy matching (ignore whitespace/reordering)")
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

    Display added, removed, or modified log entries between two files. Supports
    filtering, colorized output, and various comparison modes.
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


@cli.command(epilog="""Examples:

  pogtool merge app1.log app2.log
    → Merge two logs to stdout

  pogtool merge *.log --tag --output merged.log
    → Merge with filename tags to output file

  pogtool merge app1.log app2.log --normalize-timestamps --deduplicate
    → Normalize timestamps and deduplicate

  pogtool merge app1.log app2.log --follow
    → Stream mode for live merging
""")
@click.argument("files", nargs=-1, type=click.Path(exists=True, readable=True))
@click.option("-o", "--output", type=click.Path(), help="Output file (default: stdout)")
@click.option("-t", "--tag", is_flag=True, help="Add filename as tag/column to each entry")
@click.option("-n", "--normalize-timestamps", is_flag=True, help="Normalize timestamps to standard format")
@click.option("-d", "--deduplicate", is_flag=True, help="Remove duplicate entries")
@click.option("-f", "--follow", is_flag=True, help="Stream mode: continuously merge growing files")
@click.option("-C", "--compressed", is_flag=True, help="Support compressed input files (.gz)")
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