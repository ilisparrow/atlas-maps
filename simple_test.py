#!/usr/bin/env python3
"""Simple test to trace through page generation with real GPX data."""

import gpxpy
from page_generation import put_tiles_in_pages, get_filled_pages

def simple_lat_long_to_tile(lat, lon):
    """Simplified tile calculation (just for testing page order)."""
    # Very simplified - just use lat/lon as rough tile coordinates
    import math
    zoom = 15
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def test_gpx_page_order():
    """Test that pages follow GPS track order."""
    gpx_file = 'gpx_files/[Hard]viarhona.gpx'

    print(f"Loading {gpx_file}...")
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f)

    # Collect all tiles in GPS order
    tiles_ordered = []
    seen = set()
    point_count = 0

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                tile = simple_lat_long_to_tile(point.latitude, point.longitude)
                if tile not in seen:
                    tiles_ordered.append(tile)
                    seen.add(tile)
                point_count += 1

    print(f"Total GPS points: {point_count}")
    print(f"Unique tiles: {len(tiles_ordered)}")
    print(f"First 10 tiles in GPS order: {tiles_ordered[:10]}")
    print(f"Last 10 tiles in GPS order: {tiles_ordered[-10:]}")

    # Generate pages
    NUMBER_ROWS = 14
    NUMBER_COLUMNS = 9
    pages = put_tiles_in_pages(tiles_ordered, NUMBER_ROWS, NUMBER_COLUMNS)

    print(f"\nGenerated {len(pages)} pages")

    for i, page in enumerate(pages[:5]):  # Show first 5 pages
        print(f"\nPage {i+1}:")
        print(f"  Contains {len(page)} tiles")
        print(f"  First tile: {page[0]}")
        print(f"  Last tile: {page[-1]}")

        # Check if this page's first tile appears early in GPS track
        first_tile_index = tiles_ordered.index(page[0])
        print(f"  First tile appears at position {first_tile_index}/{len(tiles_ordered)} in GPS track")

    # Check chronological order of pages
    print("\n=== CHRONOLOGICAL ORDER CHECK ===")
    page_first_indices = []
    for i, page in enumerate(pages):
        first_tile_index = tiles_ordered.index(page[0])
        page_first_indices.append((i, first_tile_index))
        print(f"Page {i+1}: first tile is at GPS position {first_tile_index}")

    # Verify pages are in chronological order
    sorted_indices = sorted(page_first_indices, key=lambda x: x[1])
    if page_first_indices == sorted_indices:
        print("\n✓ SUCCESS: Pages are in chronological GPS order!")
    else:
        print("\n✗ FAIL: Pages are OUT OF ORDER!")
        print(f"  Current order: {[p[0]+1 for p in page_first_indices]}")
        print(f"  Should be: {[p[0]+1 for p in sorted_indices]}")

if __name__ == '__main__':
    test_gpx_page_order()
