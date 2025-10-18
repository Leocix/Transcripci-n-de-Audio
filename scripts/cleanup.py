"""Limpieza de uploads/resultados antiguos.
Uso: python scripts/cleanup.py --days 7
"""
import argparse
import time
from pathlib import Path

def clean_dir(path: Path, days: int, dry: bool = False):
    now = time.time()
    cutoff = now - days * 86400
    removed = 0
    for p in path.rglob('*'):
        if p.is_file():
            try:
                mtime = p.stat().st_mtime
                if mtime < cutoff:
                    if dry:
                        print(f"Would remove: {p}")
                    else:
                        p.unlink()
                        removed += 1
            except Exception as e:
                print(f"Error removing {p}: {e}")
    return removed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--uploads', default='uploads', help='Path to uploads dir')
    parser.add_argument('--days', type=int, default=7, help='Remove files older than DAYS')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    args = parser.parse_args()

    uploads = Path(args.uploads)
    if not uploads.exists():
        print(f"Uploads path not found: {uploads}")
        raise SystemExit(1)

    results_dir = uploads / 'results'
    jobs_failed = uploads / 'jobs' / 'failed'

    if results_dir.exists():
        removed = clean_dir(results_dir, args.days, dry=args.dry)
        print(f"Removed {removed} result files from {results_dir}")

    if jobs_failed.exists():
        removed2 = clean_dir(jobs_failed, args.days, dry=args.dry)
        print(f"Removed {removed2} failed job files from {jobs_failed}")

    print('Done')
