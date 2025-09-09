# Pogtool - Comprehensive Log Analysis Tool

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

Pogtool is a powerful command-line tool for analyzing, comparing, and merging log files. It provides comprehensive statistics, intelligent comparison capabilities, and chronological merging with support for various log formats and output options.

## 🚀 Features

### 📊 Log Statistics (`pogtool stats`)
- **Basic Features:**
  - Count lines by severity levels (INFO, WARN, ERROR, etc.)
  - Count lines matching regex patterns
  - Show total number of log lines
  
- **Intermediate Features:**
  - Group counts by time intervals (minute/hour/day)
  - Show top N most frequent log messages
  - Normalize timestamps to standard format
  
- **Advanced Features:**
  - Live/streaming mode with `--follow` (like `tail -f`)
  - Export results in JSON/CSV formats for automation
  - Aggregate statistics from multiple files

### 🔀 Log Comparison (`pogtool compare`)
- **Basic Features:**
  - Compare two log files line by line
  - Show added/removed lines in diff style
  
- **Intermediate Features:**
  - Ignore timestamps for content-only comparison
  - Compare filtered subsets (e.g., only ERROR lines)
  - Colorized diff output for better readability
  
- **Advanced Features:**
  - Summary view showing difference statistics
  - Structured JSON output for automated processing
  - Fuzzy matching (ignore whitespace/reordering)

### 🔗 Log Merging (`pogtool merge`)
- **Basic Features:**
  - Merge multiple log files by timestamp
  - Maintain chronological order
  
- **Intermediate Features:**
  - Handle different timestamp formats automatically
  - Add source file tags to merged entries
  - Deduplicate identical log entries
  
- **Advanced Features:**
  - Stream mode for live merging of growing files
  - Support compressed input files (.gz)
  - Flexible output to files, stdout, or pipes

## 📦 Usage

### Quick Start (No Installation Required)

You can run pogtool directly without installing it as a package:

```bash
git clone <repository-url>
cd pogtool
python pogtool.py --help
```

### Requirements
- Python 3.8 or higher
- Dependencies: `click`, `python-dateutil`, `colorama`

Install dependencies:
```bash
pip install click python-dateutil colorama
```

## 🔧 Usage

### Statistics Analysis

```bash
# Count log levels in a single file
python pogtool.py stats app.log --levels

# Count log levels across multiple files
python pogtool.py stats app1.log app2.log --levels

# Group errors by minute
python pogtool.py stats app.log --group-by minute --only ERROR

# Top 5 recurring log messages
python pogtool.py stats app.log --top 5

# Count specific patterns (timeouts & failed requests)
python pogtool.py stats app.log -e "timeout" -e "failed"

# Export stats as JSON (machine-readable)
python pogtool.py stats app.log --levels --json

# Live mode: update stats as log grows
python pogtool.py stats app.log --follow --levels
```

### File Comparison

```bash
# Show differences between two logs
python pogtool.py compare old.log new.log

# Only compare ERROR entries
python pogtool.py compare old.log new.log --only ERROR

# Ignore timestamps, compare only messages
python pogtool.py compare old.log new.log --ignore-timestamps

# Colorized diff output
python pogtool.py compare old.log new.log --color

# Summary view with statistics
python pogtool.py compare old.log new.log --summary

# JSON output for automation
python pogtool.py compare old.log new.log --json
```

### Log Merging

```bash
# Merge two logs chronologically into a single file
python pogtool.py merge app1.log app2.log --output merged.log

# Merge all log files in a directory and tag by filename
python pogtool.py merge *.log --tag

# Merge logs with different timestamp formats
python pogtool.py merge apache.log json.log --normalize-timestamps

# Stream merged logs to stdout (like tailing multiple logs)
python pogtool.py merge app1.log app2.log --follow

# Deduplicate identical entries while merging
python pogtool.py merge app1.log app2.log --deduplicate
```

## 🏗️ Architecture

Pogtool follows clean architecture principles with strict separation of concerns:

### Core Components

```
pogtool/
├── core/               # Domain models and interfaces
│   ├── models.py      # LogEntry, LogLevel, StatsSummary, etc.
│   └── interfaces.py  # Abstract base classes
├── parsers/           # Log format parsers
│   ├── generic.py     # Generic log parser (regex-based)
│   └── common.py      # Apache/Nginx Common Log Format
├── processors/        # Log processing logic
│   └── __init__.py    # StandardLogProcessor
├── formatters/        # Output formatters
│   ├── text.py        # Human-readable text output
│   ├── json.py        # JSON output
│   └── csv.py         # CSV output
├── readers.py         # File reading strategies
├── commands/          # Command implementations
│   ├── stats.py       # Statistics command
│   ├── compare.py     # Comparison command
│   └── merge.py       # Merge command
└── cli.py            # CLI entry point
```

### Design Principles

- **SOLID Principles**: Single responsibility, open/closed, interface segregation
- **Dependency Injection**: Components are loosely coupled through interfaces
- **Strategy Pattern**: Pluggable parsers, formatters, and file readers
- **Command Pattern**: Each CLI command is a separate, testable class
- **Strict Typing**: Full type hints for better maintainability

## 🎯 Log Format Support

### Automatically Detected Formats

- **Generic Logs**: Timestamp + Level + Message patterns
- **Apache/Nginx Common Log Format**: Web server access logs
- **Syslog Format**: Standard system logging format
- **JSON Logs**: Structured JSON log entries
- **Custom Formats**: Extensible parser system

### Timestamp Formats Supported

- ISO 8601: `2023-09-09T23:20:15.123Z`
- Common: `2023-09-09 23:20:15`
- Apache: `09/Sep/2023:23:20:15 +0000`
- Syslog: `Sep  9 23:20:15`
- Time only: `23:20:15`

## 📈 Examples

### Real-world Log Analysis

```bash
# Analyze web server logs for errors
pogtool stats access.log --levels --only ERROR --json > error_stats.json

# Compare logs before and after deployment
pogtool compare pre-deploy.log post-deploy.log --ignore-timestamps --summary

# Merge logs from multiple servers with source tagging
pogtool merge server1.log server2.log server3.log --tag --output combined.log

# Monitor live application logs for patterns
pogtool stats app.log --follow -e "OutOfMemory" -e "timeout" --top 10
```

### Integration with Other Tools

```bash
# Export stats to CSV for spreadsheet analysis
pogtool stats app.log --levels --csv > stats.csv

# Pipe merged logs to grep for further filtering
pogtool merge *.log | grep "ERROR" | head -20

# JSON output for automated monitoring
pogtool stats app.log --levels --json | jq '.level_counts.ERROR'
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pogtool --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests with verbose output
pytest -v
```

## 🔍 Advanced Features

### Live Monitoring
- Real-time statistics updates with `--follow`
- Screen clearing and timestamp updates
- Graceful handling of Ctrl+C interruption

### Format Detection
- Automatic parser selection based on log content
- Fallback to generic parsing for unknown formats
- Support for mixed log formats in single analysis

### Performance Optimization
- Streaming processing for large files
- Memory-efficient iteration over log entries
- Lazy evaluation where possible

### Error Handling
- Graceful handling of malformed log lines
- Informative error messages
- Continuation on non-fatal errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with proper tests
4. Ensure code quality: `black`, `isort`, `mypy`, `flake8`
5. Run tests: `pytest`
6. Submit a pull request

### Code Quality Standards

- **Type Hints**: All functions must have proper type annotations
- **Testing**: New features require corresponding tests
- **Documentation**: Update README for user-facing changes
- **Code Style**: Follow Black and isort formatting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- 📖 **Documentation**: This README and inline help (`pogtool --help`)
- 🐛 **Bug Reports**: Open an issue with details and reproduction steps
- 💡 **Feature Requests**: Open an issue describing the desired functionality
- 📧 **Questions**: Contact the development team

## 🗺️ Roadmap

- [ ] **Enhanced Parsers**: JSON, XML, and custom format support
- [ ] **Database Output**: Direct export to databases (SQLite, PostgreSQL)
- [ ] **Web Interface**: Browser-based log analysis dashboard
- [ ] **Machine Learning**: Anomaly detection and pattern recognition
- [ ] **Distributed Processing**: Handle extremely large log files
- [ ] **Real-time Alerting**: Notifications based on log patterns

---

**Pogtool** - Making log analysis simple, powerful, and efficient! 🚀