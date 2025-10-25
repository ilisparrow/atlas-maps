#!/usr/bin/env python3
"""Generate a comprehensive report on page generation for all test datasets."""

import json
from pathlib import Path
from page_generation import put_tiles_in_pages, get_filled_pages
from datetime import datetime


def analyze_grouping(pages, tiles_ordered, config):
    """Analyze grouped pages."""
    stats = {
        'num_pages': len(pages),
        'tiles_per_page': [len(page) for page in pages],
        'chronological_order': True,
        'page_first_indices': []
    }

    # Check chronological order
    for i, page in enumerate(pages):
        if page and page[0] in tiles_ordered:
            first_tile_index = tiles_ordered.index(page[0])
            stats['page_first_indices'].append(first_tile_index)

    # Verify order
    stats['chronological_order'] = (stats['page_first_indices'] == sorted(stats['page_first_indices']))

    return stats


def analyze_filled_pages(filled_pages, config):
    """Analyze filled pages and overlaps."""
    expected_size = config['NUMBER_COLUMNS'] * config['NUMBER_ROWS']

    stats = {
        'num_filled_pages': len(filled_pages),
        'overlaps': []
    }

    # Calculate overlaps
    for i in range(len(filled_pages) - 1):
        tiles_i = set(tile for row in filled_pages[i] for tile in row)
        tiles_next = set(tile for row in filled_pages[i+1] for tile in row)

        overlap = tiles_i.intersection(tiles_next)
        overlap_count = len(overlap)
        overlap_pct = (overlap_count / expected_size) * 100

        stats['overlaps'].append({
            'page_pair': (i+1, i+2),
            'count': overlap_count,
            'percentage': overlap_pct
        })

    return stats


def generate_report_for_dataset(name, data, config):
    """Generate a report for a single dataset."""
    tiles = [tuple(t) for t in data['tiles']]

    print(f"\n{'='*70}")
    print(f"REPORT: {name}")
    print(f"{'='*70}")
    print(f"Source: {data['source']}")
    print(f"Total GPS Points: {data['total_points']:,}")
    print(f"Unique Tiles: {data['unique_tiles']:,}")

    # Run processing
    pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])
    filled_pages = get_filled_pages(tiles, config['NUMBER_COLUMNS'], config['NUMBER_ROWS'])

    # Analyze
    group_stats = analyze_grouping(pages, tiles, config)
    filled_stats = analyze_filled_pages(filled_pages, config)

    # Print report
    print(f"\n--- GROUPING ---")
    print(f"  Pages Generated: {group_stats['num_pages']}")
    print(f"  Chronological Order: {'✓ YES' if group_stats['chronological_order'] else '✗ NO'}")

    if group_stats['tiles_per_page']:
        print(f"  Tiles per Page:")
        print(f"    Min: {min(group_stats['tiles_per_page'])}")
        print(f"    Max: {max(group_stats['tiles_per_page'])}")
        print(f"    Avg: {sum(group_stats['tiles_per_page'])/len(group_stats['tiles_per_page']):.1f}")

    print(f"\n--- FILLED PAGES ---")
    print(f"  Total Pages: {filled_stats['num_filled_pages']}")
    print(f"  Tiles per Page: {config['NUMBER_COLUMNS']}×{config['NUMBER_ROWS']} = "
          f"{config['NUMBER_COLUMNS']*config['NUMBER_ROWS']} (constant)")

    if filled_stats['overlaps']:
        avg_overlap_count = sum(o['count'] for o in filled_stats['overlaps']) / len(filled_stats['overlaps'])
        avg_overlap_pct = sum(o['percentage'] for o in filled_stats['overlaps']) / len(filled_stats['overlaps'])

        print(f"\n--- OVERLAP ANALYSIS ---")
        print(f"  Consecutive Page Pairs: {len(filled_stats['overlaps'])}")
        print(f"  Average Overlap: {avg_overlap_count:.1f} tiles ({avg_overlap_pct:.1f}%)")

        if len(filled_stats['overlaps']) <= 10:
            print(f"  Detailed Breakdown:")
            for overlap in filled_stats['overlaps']:
                print(f"    Pages {overlap['page_pair'][0]} & {overlap['page_pair'][1]}: "
                      f"{overlap['count']} tiles ({overlap['percentage']:.1f}%)")
        else:
            print(f"  Sample (first 5 pairs):")
            for overlap in filled_stats['overlaps'][:5]:
                print(f"    Pages {overlap['page_pair'][0]} & {overlap['page_pair'][1]}: "
                      f"{overlap['count']} tiles ({overlap['percentage']:.1f}%)")
            print(f"  ... and {len(filled_stats['overlaps'])-5} more pairs")

            # Show min, max overlap
            min_overlap = min(filled_stats['overlaps'], key=lambda x: x['percentage'])
            max_overlap = max(filled_stats['overlaps'], key=lambda x: x['percentage'])
            print(f"  Min Overlap: Pages {min_overlap['page_pair'][0]} & {min_overlap['page_pair'][1]} "
                  f"({min_overlap['percentage']:.1f}%)")
            print(f"  Max Overlap: Pages {max_overlap['page_pair'][0]} & {max_overlap['page_pair'][1]} "
                  f"({max_overlap['percentage']:.1f}%)")
    else:
        print(f"  No overlap (single page or completely separate pages)")

    return {
        'name': name,
        'pages': group_stats['num_pages'],
        'chronological': group_stats['chronological_order'],
        'avg_overlap_pct': sum(o['percentage'] for o in filled_stats['overlaps']) / len(filled_stats['overlaps'])
                           if filled_stats['overlaps'] else 0
    }


def main():
    """Generate reports for all test datasets."""
    fixture_path = Path('tests/test_fixtures.json')

    if not fixture_path.exists():
        print("Error: Test fixtures not found. Run extract_test_data.py first.")
        return

    with open(fixture_path, 'r') as f:
        test_data = json.load(f)

    config = {
        'NUMBER_ROWS': 14,
        'NUMBER_COLUMNS': 9
    }

    print("="*70)
    print("PAGE GENERATION ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Grid Configuration: {config['NUMBER_COLUMNS']}×{config['NUMBER_ROWS']} tiles per page")
    print("="*70)

    summaries = []
    for name, data in test_data.items():
        summary = generate_report_for_dataset(name, data, config)
        summaries.append(summary)

    # Overall summary
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"{'Dataset':<20} {'Pages':>8} {'Chronological':>15} {'Avg Overlap':>15}")
    print("-"*70)

    for summary in summaries:
        print(f"{summary['name']:<20} {summary['pages']:>8} "
              f"{'✓' if summary['chronological'] else '✗':>15} "
              f"{summary['avg_overlap_pct']:>14.1f}%")

    print(f"{'='*70}")
    print("\n✓ Report generation complete!")


if __name__ == '__main__':
    main()
