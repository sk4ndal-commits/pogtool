"""
Core domain models and interfaces for pogtool.

This module contains the fundamental abstractions and domain models
used throughout the application.
"""

from pogtool.core.models import LogEntry, LogLevel, TimeInterval
from pogtool.core.interfaces import (
    Command,
    LogParser,
    LogFormatter,
    LogProcessor,
    FileReader,
)

__all__ = [
    "LogEntry",
    "LogLevel", 
    "TimeInterval",
    "Command",
    "LogParser",
    "LogFormatter",
    "LogProcessor",
    "FileReader",
]