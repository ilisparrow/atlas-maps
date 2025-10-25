#!/usr/bin/env python3
"""Test script to see page generation with real GPX files."""

import asyncio
import gpxpy
from utils import main

async def test_hard_gpx():
    """Test with the [Hard]viarhona.gpx file."""
    gpx_file = 'gpx_files/[Hard]viarhona.gpx'

    print(f"Loading {gpx_file}...")
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f)

    print(f"Tracks: {len(gpx.tracks)}")
    for i, track in enumerate(gpx.tracks):
        print(f"  Track {i}: {len(track.segments)} segments")
        for j, segment in enumerate(track.segments):
            print(f"    Segment {j}: {len(segment.points)} points")
            if len(segment.points) > 0:
                first = segment.points[0]
                last = segment.points[-1]
                print(f"      First point: ({first.latitude}, {first.longitude})")
                print(f"      Last point: ({last.latitude}, {last.longitude})")

    print("\nGenerating PDF...")
    pdf_path = await main(gpx, tile_source="IGN", line_color="#B700FF")

    if pdf_path:
        print(f"✓ PDF generated: {pdf_path}")
    else:
        print("✗ No PDF generated (empty track?)")

if __name__ == '__main__':
    asyncio.run(test_hard_gpx())
