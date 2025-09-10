#!/usr/bin/env python3
"""Build script to create Windows executable from pogtool using PyInstaller."""

import os
import sys
import subprocess
from pathlib import Path


def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install PyInstaller: {e}")
            return False


def build_executable():
    """Build the Windows executable using PyInstaller."""
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # PyInstaller command with options
    cmd = [
        "pyinstaller",
        "--onefile",             # Create a single executable file
        "--console",             # Keep console window (for command-line tool)
        "--name", "pogtool",     # Name of the executable
        "--distpath", "dist",    # Output directory
        "--workpath", "build",   # Temporary build directory
        "--specpath", ".",       # Location for .spec file
        "--clean",               # Clean PyInstaller cache before building
        "--noconfirm",           # Replace output directory without confirmation
        "--hidden-import", "click",           # Ensure click is included
        "--hidden-import", "colorama",        # Ensure colorama is included
        "--hidden-import", "dateutil",        # Ensure dateutil is included
        "--hidden-import", "pogtool.commands.compare",  # Include all command modules
        "--hidden-import", "pogtool.commands.merge",
        "--hidden-import", "pogtool.commands.stats",
        "--hidden-import", "pogtool.formatters.csv",    # Include all formatter modules
        "--hidden-import", "pogtool.formatters.json",
        "--hidden-import", "pogtool.formatters.text",
        "--hidden-import", "pogtool.parsers.common",    # Include all parser modules
        "--hidden-import", "pogtool.parsers.generic",
        "pogtool.py"             # Main Python script
    ]
    
    print("Building Windows executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print("\nBuild output:")
        print(result.stdout)
        
        # Check if executable was created
        exe_path = Path("dist/pogtool.exe")
        if exe_path.exists():
            print(f"\n✅ Executable created successfully: {exe_path.absolute()}")
            print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        else:
            print("❌ Executable file not found in expected location")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Main build function."""
    print("=== Windows Executable Builder for pogtool ===\n")
    
    # Check if we're on Windows (optional - PyInstaller works on other platforms too)
    print(f"Current platform: {sys.platform}")
    if sys.platform != "win32":
        print("Note: Building on non-Windows platform. The executable will still be for Windows.")
    
    # Install PyInstaller if needed
    if not install_pyinstaller():
        print("Cannot proceed without PyInstaller.")
        return 1
    
    # Build the executable
    if build_executable():
        print("\n🎉 Build completed successfully!")
        print("\nTo use the executable:")
        print("1. Navigate to the 'dist' folder")
        print("2. Copy pogtool.exe to your desired location")
        print("3. Add the location to your Windows PATH (optional)")
        print("4. Use: pogtool.exe [command] [options] [files...]")
        print("\nAvailable commands:")
        print("  - pogtool.exe stats app.log --levels")
        print("  - pogtool.exe compare old.log new.log")
        print("  - pogtool.exe merge app1.log app2.log")
        print("  - pogtool.exe --help (for more information)")
        return 0
    else:
        print("\n💥 Build failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())