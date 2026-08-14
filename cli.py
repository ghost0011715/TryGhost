#!/usr/bin/env python3
"""
CLI Entry Point for FileScanner
"""

import argparse
import sys
from main import FileAnalysisApp
from file_scanner import FileScanner, FileDuplicateFinder
from utils import print_table, format_bytes, print_section
import json


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FileScanner with ChatGPT Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --scan .                    # Scan current directory
  python cli.py --scan /path/to/files       # Scan specific directory
  python cli.py --scan . --find-duplicates  # Scan and find duplicates
  python cli.py --interactive               # Start interactive mode
        """
    )
    
    parser.add_argument(
        "--scan",
        type=str,
        metavar="PATH",
        help="Scan directory for files"
    )
    parser.add_argument(
        "--find-duplicates",
        action="store_true",
        help="Find duplicate files after scanning"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze files with ChatGPT"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive CLI mode"
    )
    parser.add_argument(
        "--output",
        type=str,
        metavar="FILE",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--filter-ext",
        type=str,
        metavar="EXT",
        help="Filter files by extension (e.g., .txt,.py)"
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files in scan"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Interactive mode
    if args.interactive:
        try:
            app = FileAnalysisApp()
            app.start_interactive()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        return
    
    # Scan mode
    if args.scan:
        try:
            print_section(f"Scanning: {args.scan}")
            
            scanner = FileScanner(args.scan)
            files = scanner.scan_directory(include_hidden=args.include_hidden)
            
            # Filter by extension if specified
            if args.filter_ext:
                extensions = [f".{ext}" if not ext.startswith('.') else ext 
                             for ext in args.filter_ext.split(',')]
                files = scanner.filter_by_extension(files, extensions)
            
            print(f"✅ Found {len(files)} files\n")
            
            # Show statistics
            stats = scanner.get_statistics(files)
            print("📊 Statistics:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total size: {format_bytes(stats['total_size_mb'] * 1024 * 1024)}")
            
            if stats.get('largest_file'):
                largest = stats['largest_file']
                print(f"  Largest file: {largest['name']} ({format_bytes(largest['size_bytes'])})")
            
            print(f"  File types: {len(stats['by_extension'])}")
            
            # Show file type breakdown
            print("\n  By extension:")
            for ext, count in sorted(stats['by_extension'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    {ext}: {count} files")
            
            # Find duplicates if requested
            if args.find_duplicates:
                print_section("Duplicate Analysis")
                finder = FileDuplicateFinder()
                duplicates = finder.find_duplicates(files)
                
                if duplicates:
                    print(f"⚠️ Found {len(duplicates)} duplicate file groups:\n")
                    for i, (group_key, group_files) in enumerate(list(duplicates.items())[:5], 1):
                        print(f"  {i}. {group_key}")
                        for f in group_files:
                            print(f"     - {f['path']} ({format_bytes(f['size_bytes'])})")
                else:
                    print("✅ No duplicate files found!")
            
            # Show sample files
            print_section("Sample Files")
            sample_data = []
            for f in files[:10]:
                sample_data.append({
                    "Name": f['name'],
                    "Size": format_bytes(f['size_bytes']),
                    "Type": f['extension'],
                    "Path": f['path'][:40] + "..." if len(f['path']) > 40 else f['path']
                })
            print_table(sample_data)
            
            if len(files) > 10:
                print(f"\n... and {len(files) - 10} more files")
            
            # Save to file if requested
            if args.output:
                output_data = {
                    "summary": stats,
                    "files": files,
                    "duplicates": {k: v for k, v in finder.find_duplicates(files).items()} if args.find_duplicates else {}
                }
                
                try:
                    with open(args.output, 'w') as f:
                        json.dump(output_data, f, indent=2)
                    print(f"\n✅ Results saved to: {args.output}")
                except Exception as e:
                    print(f"❌ Error saving to file: {str(e)}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
