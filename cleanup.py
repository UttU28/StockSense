#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path

def get_project_root():
    script_path = Path(__file__).resolve()
    return script_path.parent

def remove_pycache(root_dir):
    removed = []
    for pycache_dir in root_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            removed.append(str(pycache_dir.relative_to(root_dir)))
        except Exception as e:
            print(f"Error removing {pycache_dir}: {e}")
    return removed

def remove_pyc_files(root_dir):
    removed = []
    patterns = ["*.pyc", "*.pyo", "*.pyd"]
    for pattern in patterns:
        for file_path in root_dir.rglob(pattern):
            try:
                file_path.unlink()
                removed.append(str(file_path.relative_to(root_dir)))
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    return removed

def remove_temp_files(root_dir):
    removed = []
    patterns = ["*.tmp", "*.temp", "*.bak", "*.backup", "*~", "*.swp", "*.swo"]
    for pattern in patterns:
        for file_path in root_dir.rglob(pattern):
            try:
                file_path.unlink()
                removed.append(str(file_path.relative_to(root_dir)))
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    return removed

def remove_os_files(root_dir):
    removed = []
    patterns = [".DS_Store", "Thumbs.db", "desktop.ini", "._*", ".AppleDouble", ".LSOverride"]
    for pattern in patterns:
        for file_path in root_dir.rglob(pattern):
            try:
                file_path.unlink()
                removed.append(str(file_path.relative_to(root_dir)))
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    return removed

def remove_cache_dirs(root_dir):
    removed = []
    cache_dirs = [
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".cache",
        ".tox",
        ".ruff_cache",
    ]
    for cache_dir in cache_dirs:
        for dir_path in root_dir.rglob(cache_dir):
            if dir_path.is_dir():
                try:
                    shutil.rmtree(dir_path)
                    removed.append(str(dir_path.relative_to(root_dir)))
                except Exception as e:
                    print(f"Error removing {dir_path}: {e}")
    return removed

def remove_build_dirs(root_dir, include_build=True):
    removed = []
    build_dirs = []
    if include_build:
        build_dirs = ["build", "dist", "*.egg-info", "*.egg"]
    for pattern in build_dirs:
        if "*" in pattern:
            for dir_path in root_dir.rglob(pattern):
                if dir_path.is_dir():
                    try:
                        shutil.rmtree(dir_path)
                        removed.append(str(dir_path.relative_to(root_dir)))
                    except Exception as e:
                        print(f"Error removing {dir_path}: {e}")
        else:
            for dir_path in root_dir.rglob(pattern):
                if dir_path.is_dir():
                    try:
                        shutil.rmtree(dir_path)
                        removed.append(str(dir_path.relative_to(root_dir)))
                    except Exception as e:
                        print(f"Error removing {dir_path}: {e}")
    return removed

def remove_logs(root_dir, include_logs=True):
    removed = []
    if include_logs:
        for log_file in root_dir.rglob("*.log"):
            try:
                log_file.unlink()
                removed.append(str(log_file.relative_to(root_dir)))
            except Exception as e:
                print(f"Error removing {log_file}: {e}")
    return removed

def main():
    root_dir = get_project_root()
    print("=" * 60)
    print("StockSense Cleanup Script")
    print("=" * 60)
    print(f"Cleaning: {root_dir}")
    print()
    print("Starting cleanup...\n")
    pycache_dirs = remove_pycache(root_dir)
    pyc_files = remove_pyc_files(root_dir)
    temp_files = remove_temp_files(root_dir)
    os_files = remove_os_files(root_dir)
    cache_dirs = remove_cache_dirs(root_dir)
    build_dirs = remove_build_dirs(root_dir, include_build=True)
    log_files = remove_logs(root_dir, include_logs=True)
    print("\n" + "=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"__pycache__ directories removed: {len(pycache_dirs)}")
    print(f".pyc/.pyo/.pyd files removed: {len(pyc_files)}")
    print(f"Temporary files removed: {len(temp_files)}")
    print(f"OS files removed: {len(os_files)}")
    print(f"Cache directories removed: {len(cache_dirs)}")
    print(f"Build directories removed: {len(build_dirs)}")
    print(f"Log files removed: {len(log_files)}")
    total = (
        len(pycache_dirs)
        + len(pyc_files)
        + len(temp_files)
        + len(os_files)
        + len(cache_dirs)
        + len(build_dirs)
        + len(log_files)
    )
    print(f"\nTotal items removed: {total}")
    print("=" * 60)
    print("Cleanup complete! Thank you.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during cleanup: {e}")
        sys.exit(1)
