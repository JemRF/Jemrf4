"""distribute.py

Create usb folders (../usb0 .. ../usb4) and copy serial_mon.py and rf_config.py
from parent directory into each usb folder. Intended to be run from
the `rf4setup` directory, but resolves sources relative to the script's
parent directory so it's robust.

Usage:
  python distribute.py            # actually copy
  python distribute.py --dry-run  # show actions without changing filesystem

Options:
  --src FILE [FILE ...]   list of source files relative to project root (parent of rf4setup)
  --dest DIR [DIR ...]    list of destination directories (default: usb0 usb1 usb2 usb3 usb4)
  --dry-run               show actions without creating/copying
"""

from pathlib import Path
import shutil
import sys
import argparse
import re
import os
import stat


def backup_existing(path: Path, dry_run: bool = False) -> bool:
    """If path exists, rename it to path + '.org' (or '.org.N' if needed).
    Returns True if backup succeeded or file did not exist; False on failure.
    """
    if not path.exists():
        return True

    base = str(path) + '.org'
    candidate = Path(base)
    i = 0
    while candidate.exists():
        i += 1
        candidate = Path(f"{base}.{i}")
        if i > 100:
            print(f"Could not find backup name for {path}", file=sys.stderr)
            return False

    if dry_run:
        print(f"DRY RUN: would rename existing {path} -> {candidate}")
        return True

    try:
        path.rename(candidate)
        print(f"Renamed existing {path} -> {candidate}")
        return True
    except Exception as e:
        print(f"Failed to rename existing {path} -> {candidate}: {e}", file=sys.stderr)
        return False


def copy_to_usb_dirs(script_dir: Path, sources, usb_dirs, dry_run: bool = False):
    project_root = script_dir.parent

    # Resolve sources to absolute paths
    resolved_sources = []
    for s in sources:
        p = Path(s)
        if not p.is_absolute():
            # Resolve source paths relative to the current script directory (rf4setup)
            p = script_dir / p
        resolved_sources.append(p)

    # Also copy each source into the parent of project root (up one level)
    for src in resolved_sources:
        if not src.exists():
            print(f"Warning: source not found at expected location: {src}", file=sys.stderr)

        # Use the source from the current (project_root) location for the first copy
        source_to_use = src

        # destination is one level above the script directory (rf4setup's parent)
        dest_root = script_dir.parent / src.name
        if dry_run:
            print(f"DRY RUN: would copy {source_to_use} -> {dest_root}")
            continue

        # If source and destination are the same file, skip copying
        try:
            if source_to_use.resolve() == dest_root.resolve():
                print(f"Source and destination are the same ({source_to_use}); skipping copy")
                continue
        except Exception:
            # ignore resolve errors and proceed
            pass

        # If destination exists, back it up by renaming to .org (or .org.N)
        if dest_root.exists():
            ok = backup_existing(dest_root, dry_run=dry_run)
            if not ok:
                print(f"Skipping copy for {src} because backup failed", file=sys.stderr)
                continue

        try:
            shutil.copy2(source_to_use, dest_root)
            print(f"Copied {source_to_use.name} -> {dest_root.parent}")
        except PermissionError as pe:
            print(f"PermissionError copying {source_to_use} -> {dest_root}: {pe}", file=sys.stderr)
        except Exception as e:
            print(f"Error copying {source_to_use} -> {dest_root}: {e}", file=sys.stderr)

    for usb in usb_dirs:
        dest_dir = project_root / usb
        if not dest_dir.exists():
            if dry_run:
                print(f"DRY RUN: would create directory: {dest_dir}")
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dest_dir}")
        else:
            print(f"Directory exists: {dest_dir}")

        # copy each source into dest
        for src in resolved_sources:
            if not src.exists():
                print(f"Warning: source not found, skipping: {src}", file=sys.stderr)
                continue
            dest_file = dest_dir / src.name

            # Special handling: edit rflib.py per-usb destination
            if src.name == 'rflib.py' and not dry_run:
                # read original content
                try:
                    content = src.read_text(encoding='utf-8')
                except Exception:
                    content = src.read_text()

                # determine usb number from directory name like 'usb0'
                usb_name = Path(usb).name
                mnum = re.search(r"(\d+)$", usb_name)
                usb_num = mnum.group(1) if mnum else '0'

                # remove existing ttyUSB lines to avoid duplicates
                content = re.sub(r"(?m)^\s*port\s*=\s*['\"]?/dev/ttyUSB\d+['\"]?\s*\n", "", content)

                # insert new ttyUSB line above /dev/serial0 or replace any port assignment
                pattern = re.compile(r"(?m)^(?P<indent>\s*)port\s*=\s*['\"]?/dev/serial0['\"]?.*$")
                m = pattern.search(content)
                if m:
                    indent = m.group('indent')
                    insert_line = f"\n{indent}port = '/dev/ttyUSB{usb_num}'\n"
                    # insert the new ttyUSB line after the existing serial0 line
                    new_content = content.replace(m.group(0), m.group(0) + insert_line, 1)
                else:
                    pattern2 = re.compile(r'(?m)^(?P<indent>\s*)port\s*=\s*[\'\"].*?[\'\"]?.*$')
                    m2 = pattern2.search(content)
                    if m2:
                        indent = m2.group('indent')
                        new_content = content.replace(m2.group(0), f"\n{indent}port = '/dev/ttyUSB{usb_num}'\n", 1)
                    else:
                        new_content = f"port = '/dev/ttyUSB{usb_num}'\n" + content

                # Backup existing destination instead of deleting
                ok = backup_existing(dest_file, dry_run=dry_run)
                if not ok:
                    print(f"Skipping write for {dest_file} because backup failed", file=sys.stderr)
                    continue

                try:
                    dest_file.write_text(new_content, encoding='utf-8')
                    print(f"Wrote modified rflib.py -> {dest_dir}")
                except PermissionError as pe:
                    print(f"PermissionError writing {dest_file}: {pe}", file=sys.stderr)
                except Exception as e:
                    print(f"Error writing {dest_file}: {e}", file=sys.stderr)
                continue

            # Normal copy for other files
            if dry_run:
                print(f"DRY RUN: would copy {src} -> {dest_file}")
                continue

            # Backup existing destination instead of deleting
            ok = backup_existing(dest_file, dry_run=dry_run)
            if not ok:
                print(f"Skipping copy for {src} -> {dest_file} because backup failed", file=sys.stderr)
                continue

            try:
                shutil.copy2(src, dest_file)
                print(f"Copied {src.name} -> {dest_dir}")
            except PermissionError as pe:
                print(f"PermissionError copying {src} -> {dest_file}: {pe}", file=sys.stderr)
            except Exception as e:
                print(f"Error copying {src} -> {dest_file}: {e}", file=sys.stderr)


def cleanup_backups(script_dir: Path, usb_dirs, dry_run: bool = False):
    """Remove backup files matching .org and .org.N in the parent and usb directories."""
    project_root = script_dir.parent
    targets = [project_root]
    for usb in usb_dirs:
        targets.append(project_root / usb)

    for t in targets:
        if not t.exists():
            continue
        try:
            for f in t.iterdir():
                if not f.is_file():
                    continue
                name = f.name
                if name.endswith('.org') or '.org.' in name:
                    if dry_run:
                        print(f"DRY RUN: would remove backup file: {f}")
                    else:
                        try:
                            f.unlink()
                            print(f"Removed backup file: {f}")
                        except Exception as e:
                            print(f"Failed to remove backup {f}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error scanning for backups in {t}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Distribute files to usb folders')
    parser.add_argument('--dry-run', action='store_true', help='Show actions without making changes')
    parser.add_argument('--clean-backups', action='store_true', help='Remove .org* backup files after copying')
    parser.add_argument('--src', nargs='+', help='Source files relative to project root (default serial_mon.py rf_config.py)')
    parser.add_argument('--dest', nargs='+', help='Destination directories under project root (default usb0 usb1 usb2 usb3 usb4)')
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent

    default_sources = ['serial_mon.py', 'rf_config.py', 'rf4_library.py', 'bme280.py', 'rflib.py']
    sources = args.src if args.src else default_sources

    default_dests = [f'usb{i}' for i in range(5)]
    dests = args.dest if args.dest else default_dests

    copy_to_usb_dirs(script_dir, sources, dests, dry_run=args.dry_run)

    if args.clean_backups:
        cleanup_backups(script_dir, dests, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
