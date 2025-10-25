#!/usr/bin/env python3
"""Extract real tile sequences from GPX files to use as test fixtures."""

import json
import math
import gpxpy

def simple_lat_long_to_tile(lat, lon, zoom=15):
    """Convert latitude/longitude to tile coordinates."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def extract_tiles_from_gpx(gpx_path, max_tiles=None):
    """Extract ordered list of unique tiles from GPX file."""
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)

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

                if max_tiles and len(tiles_ordered) >= max_tiles:
                    break
            if max_tiles and len(tiles_ordered) >= max_tiles:
                break
        if max_tiles and len(tiles_ordered) >= max_tiles:
            break

    return {
        'tiles': tiles_ordered,
        'total_points': point_count,
        'unique_tiles': len(tiles_ordered),
        'source': gpx_path
    }

def main():
    """Extract test fixtures from all GPX files."""
    test_data = {}

    # Small dataset - first 50 tiles
    print("Extracting small test data (50 tiles)...")
    small_data = extract_tiles_from_gpx('gpx_files/[Hard]viarhona.gpx', max_tiles=50)
    test_data['small_linear'] = small_data
    print(f"  {small_data['unique_tiles']} tiles from {small_data['total_points']} points")

    # Medium dataset - first 200 tiles
    print("Extracting medium test data (200 tiles)...")
    medium_data = extract_tiles_from_gpx('gpx_files/[Hard]viarhona.gpx', max_tiles=200)
    test_data['medium_linear'] = medium_data
    print(f"  {medium_data['unique_tiles']} tiles from {medium_data['total_points']} points")

    # Full dataset
    print("Extracting full test data...")
    full_data = extract_tiles_from_gpx('gpx_files/[Hard]viarhona.gpx')
    test_data['full_viarhona'] = full_data
    print(f"  {full_data['unique_tiles']} tiles from {full_data['total_points']} points")

    # Try mini map if exists
    try:
        print("Extracting mini_map data...")
        mini_data = extract_tiles_from_gpx('gpx_files/[Standard]mini_map.gpx')
        test_data['mini_map'] = mini_data
        print(f"  {mini_data['unique_tiles']} tiles from {mini_data['total_points']} points")
    except FileNotFoundError:
        print("  mini_map.gpx not found, skipping")

    # Save to JSON
    output_file = 'tests/test_fixtures.json'
    with open(output_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"\n✓ Test fixtures saved to {output_file}")
    print(f"  Total datasets: {len(test_data)}")

if __name__ == '__main__':
    main()
