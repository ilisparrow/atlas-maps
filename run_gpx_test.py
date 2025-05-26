import asyncio
import gpxpy
import gpxpy.gpx
import pandas as pd # Needed for the processing logic
import numpy as np  # Needed for the processing logic
from collections import defaultdict # Needed for gpx_points

# Assuming utils.py is in the root and contains vectorized_lat_long_to_osm_tile
# We need to simulate the tile calculation part for OSM-like behavior.
from utils import vectorized_lat_long_to_osm_tile # Directly import the OSM version

async def run_isolated_gpx_analysis():
    gpx_file_path = "gpx_files/[Standard]mini_map.gpx"
    total_gpx_points = 0

    try:
        print(f"Loading GPX file: {gpx_file_path}")
        with open(gpx_file_path, 'r') as f:
            gpx = gpxpy.parse(f)
        print("GPX file loaded successfully.")

        # --- Start of logic adapted from utils.main for tile calculation ---
        ordered_unique_track_tiles = []
        seen_tiles_for_order = set()
        all_track_tiles_set = set()
        # gpx_points_dict = defaultdict(list) # Not strictly needed for counts, but part of original logic
        # point_index = 0 # Not strictly needed for counts

        for track in gpx.tracks:
            for segment in track.segments:
                total_gpx_points += len(segment.points)
                if not segment.points:
                    continue

                # Prepare lats and longs for vectorized processing
                lats = np.array([p.latitude for p in segment.points])
                longs = np.array([p.longitude for p in segment.points])
                
                # Directly use the OSM tile calculation function (zoom 15 is default in it)
                # This bypasses the TILE_SOURCE switching in get_tile_number_from_coord
                cols, rows, _, _ = vectorized_lat_long_to_osm_tile(lats, longs) 
                
                for i in range(len(cols)):
                    col, row = cols[i], rows[i]
                    # current_point = segment.points[i] # Not needed for counts

                    all_track_tiles_set.add((col, row))
                    if (col, row) not in seen_tiles_for_order:
                        ordered_unique_track_tiles.append((col, row))
                        seen_tiles_for_order.add((col, row))
                    
                    # gpx_points_dict[(col, row)].append((offset_xs[i], offset_ys[i], current_point.latitude, point_index))
                    # point_index += 1
        # --- End of adapted logic ---

        print(f"Total GPX points: {total_gpx_points}")
        print(f"Number of unique tiles visited (all_track_tiles_set): {len(all_track_tiles_set)}")
        print(f"Length of ordered unique track tiles list: {len(ordered_unique_track_tiles)}")
        
        # Verify all tiles in ordered list are in the set (sanity check)
        if len(ordered_unique_track_tiles) == len(set(ordered_unique_track_tiles)):
            print("Sanity check: ordered_unique_track_tiles contains unique elements: PASS")
        else:
            print("Sanity check: ordered_unique_track_tiles contains unique elements: FAIL")
        
        if set(ordered_unique_track_tiles) == all_track_tiles_set:
            print("Sanity check: ordered list and set cover the same tiles: PASS")
        else:
            print("Sanity check: ordered list and set cover the same tiles: FAIL")


    except FileNotFoundError:
        print(f"Error: GPX file not found at {gpx_file_path}")
    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_isolated_gpx_analysis())
