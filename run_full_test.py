#!/usr/bin/env python3
"""
Comprehensive test runner that:
- Uses actual GPX processing functions
- Generates PDFs
- Profiles each step
- Saves detailed reports
"""

import asyncio
import gpxpy
import time
import json
from pathlib import Path
from datetime import datetime
from utils import main, vectorized_get_tile_number_from_coord
from page_generation import put_tiles_in_pages, get_filled_pages
import pandas as pd
import numpy as np


class TestRunner:
    def __init__(self, output_dir="test_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    def profile_step(self, name, func, *args, **kwargs):
        """Profile a function execution."""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed

    async def profile_async_step(self, name, func, *args, **kwargs):
        """Profile an async function execution."""
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed

    def extract_tiles_real(self, gpx, tile_source="IGN"):
        """Extract tiles using the ACTUAL processing functions from utils.py"""
        list_index_found = []
        seen_tiles = set()
        gpx_points = {}
        point_index = 0

        for track in gpx.tracks:
            for segment in track.segments:
                data = pd.DataFrame([(p.latitude, p.longitude) for p in segment.points],
                                    columns=['lat', 'long'])

                cols, rows, offset_xs, offset_ys = vectorized_get_tile_number_from_coord(
                    data['lat'].values, data['long'].values, tile_source
                )

                for i, (col, row, ox, oy) in enumerate(zip(cols, rows, offset_xs, offset_ys)):
                    point = segment.points[i]

                    # Preserve chronological order
                    if (col, row) not in seen_tiles:
                        list_index_found.append((col, row))
                        seen_tiles.add((col, row))

                    point_index += 1

        return list_index_found, point_index

    async def test_gpx_file(self, gpx_path, tile_source="OSM", max_points=None):
        """Test a single GPX file with full processing pipeline."""
        gpx_name = Path(gpx_path).stem
        print(f"\n{'='*70}")
        print(f"Testing: {gpx_name}")
        print(f"{'='*70}")

        profile = {
            'gpx_file': gpx_path,
            'tile_source': tile_source,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }

        # Step 1: Load GPX
        print("Step 1: Loading GPX file...")
        start = time.time()
        with open(gpx_path, 'r') as f:
            gpx = gpxpy.parse(f)
        load_time = time.time() - start

        total_points = sum(len(seg.points) for track in gpx.tracks for seg in track.segments)
        if max_points and total_points > max_points:
            print(f"  Limiting to first {max_points} points (total: {total_points})")
            # Trim segments
            point_count = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    if point_count + len(segment.points) > max_points:
                        segment.points = segment.points[:max_points - point_count]
                        point_count = max_points
                        break
                    point_count += len(segment.points)
                if point_count >= max_points:
                    break

        profile['steps']['load_gpx'] = {
            'time': load_time,
            'total_points': total_points
        }
        print(f"  ✓ Loaded {total_points:,} GPS points in {load_time:.3f}s")

        # Step 2: Extract tiles using REAL functions
        print("\nStep 2: Extracting tiles (using actual utils.py functions)...")
        result, extract_time = self.profile_step(
            'extract_tiles',
            self.extract_tiles_real,
            gpx, tile_source
        )
        tiles, actual_point_count = result

        profile['steps']['extract_tiles'] = {
            'time': extract_time,
            'unique_tiles': len(tiles),
            'points_processed': actual_point_count
        }
        print(f"  ✓ Extracted {len(tiles)} unique tiles in {extract_time:.3f}s")
        print(f"    Points/sec: {actual_point_count/extract_time:,.0f}")

        # Step 3: Group tiles into pages
        print("\nStep 3: Grouping tiles into pages...")
        pages, group_time = self.profile_step(
            'group_pages',
            put_tiles_in_pages,
            tiles, 14, 9  # NUMBER_ROWS, NUMBER_COLUMNS
        )

        profile['steps']['group_pages'] = {
            'time': group_time,
            'num_pages': len(pages),
            'tiles_per_page': [len(p) for p in pages]
        }
        print(f"  ✓ Grouped into {len(pages)} pages in {group_time:.3f}s")
        print(f"    Avg tiles/page: {sum(len(p) for p in pages)/len(pages):.1f}")

        # Step 4: Fill pages (create 9x14 grids)
        print("\nStep 4: Filling pages with 9x14 grids...")
        filled_pages, fill_time = self.profile_step(
            'fill_pages',
            get_filled_pages,
            tiles, 9, 14  # NUMBER_COLUMNS, NUMBER_ROWS
        )

        profile['steps']['fill_pages'] = {
            'time': fill_time,
            'num_filled_pages': len(filled_pages)
        }
        print(f"  ✓ Filled {len(filled_pages)} pages in {fill_time:.3f}s")

        # Step 5: Generate PDF using REAL main function
        print("\nStep 5: Generating PDF (actual full pipeline)...")
        pdf_path, pdf_time = await self.profile_async_step(
            'generate_pdf',
            main,
            gpx, tile_source, "#B700FF"
        )

        profile['steps']['generate_pdf'] = {
            'time': pdf_time,
            'pdf_path': str(pdf_path) if pdf_path else None
        }

        if pdf_path:
            # Copy PDF to test output
            import shutil
            pdf_size = Path(pdf_path).stat().st_size
            output_pdf = self.output_dir / f"{gpx_name}_{tile_source}.pdf"
            shutil.copy(pdf_path, output_pdf)
            print(f"  ✓ Generated PDF in {pdf_time:.3f}s")
            print(f"    Size: {pdf_size/1024/1024:.2f} MB")
            print(f"    Saved to: {output_pdf}")
            profile['steps']['generate_pdf']['size_mb'] = pdf_size/1024/1024
        else:
            print(f"  ✗ PDF generation failed")

        # Calculate total time
        total_time = load_time + extract_time + group_time + fill_time + pdf_time
        profile['total_time'] = total_time

        # Verify chronological order
        print("\nStep 6: Verifying chronological order...")
        chronological = True
        page_first_indices = []
        for i, page in enumerate(pages):
            if page and page[0] in tiles:
                idx = tiles.index(page[0])
                page_first_indices.append(idx)

        if page_first_indices != sorted(page_first_indices):
            chronological = False

        profile['verification'] = {
            'chronological_order': chronological,
            'page_order': page_first_indices[:10]  # First 10 pages
        }

        print(f"  Chronological order: {'✓ PASS' if chronological else '✗ FAIL'}")

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total time: {total_time:.2f}s")
        print(f"  Load GPX:      {load_time:>8.3f}s ({load_time/total_time*100:>5.1f}%)")
        print(f"  Extract tiles: {extract_time:>8.3f}s ({extract_time/total_time*100:>5.1f}%)")
        print(f"  Group pages:   {group_time:>8.3f}s ({group_time/total_time*100:>5.1f}%)")
        print(f"  Fill pages:    {fill_time:>8.3f}s ({fill_time/total_time*100:>5.1f}%)")
        print(f"  Generate PDF:  {pdf_time:>8.3f}s ({pdf_time/total_time*100:>5.1f}%)")
        print(f"{'='*70}")

        self.results.append(profile)
        return profile

    def save_report(self):
        """Save comprehensive report."""
        report_file = self.output_dir / "test_report_latest.json"

        with open(report_file, 'w') as f:
            json.dump({
                'results': self.results
            }, f, indent=2)

        print(f"\n✓ Full report saved to: {report_file}")

        # Also create readable text report
        text_report = self.output_dir / "test_report_latest.txt"

        with open(text_report, 'w') as f:
            f.write("="*70 + "\n")
            f.write("GPX TO MAP - TEST REPORT\n")
            f.write("="*70 + "\n\n")

            for result in self.results:
                f.write(f"File: {result['gpx_file']}\n")
                f.write(f"Tile Source: {result['tile_source']}\n")
                f.write(f"Total Time: {result['total_time']:.2f}s\n\n")

                f.write("Steps:\n")
                for step_name, step_data in result['steps'].items():
                    f.write(f"  {step_name:20s}: {step_data['time']:>8.3f}s\n")

                if 'verification' in result:
                    f.write(f"\nVerification:\n")
                    f.write(f"  Chronological: {result['verification']['chronological_order']}\n")

                f.write("\n" + "-"*70 + "\n\n")

        print(f"✓ Text report saved to: {text_report}")


async def main_test():
    """Run comprehensive tests."""
    runner = TestRunner()

    print("="*70)
    print("COMPREHENSIVE GPX PROCESSING TEST SUITE")
    print("Using REAL processing functions from utils.py")
    print("="*70)

    # Test with small dataset (first 500 points)
    await runner.test_gpx_file(
        'gpx_files/[Hard]viarhona.gpx',
        tile_source='OSM',
        max_points=500
    )

    # Test with mini map (full)
    if Path('gpx_files/[Standard]mini_map.gpx').exists():
        await runner.test_gpx_file(
            'gpx_files/[Standard]mini_map.gpx',
            tile_source='OSM'
        )

    # Save comprehensive report
    runner.save_report()

    print(f"\n{'='*70}")
    print("ALL TESTS COMPLETE")
    print(f"{'='*70}")
    print(f"Output directory: {runner.output_dir}")
    print(f"PDFs generated: {len([r for r in runner.results if r['steps']['generate_pdf']['pdf_path']])}")


if __name__ == '__main__':
    asyncio.run(main_test())
