

import math

def put_tiles_in_pages(ordered_unique_track_tiles, all_track_tiles_set, NUMBER_ROWS, NUMBER_COLUMNS):
    globally_processed_track_tiles = set()
    pages = []

    for track_anchor_tile in ordered_unique_track_tiles:
        if track_anchor_tile in globally_processed_track_tiles:
            # This part of the track is already covered by a page initiated by an earlier anchor.
            continue

        page_origin_col, page_origin_row = track_anchor_tile
        
        # Calculate page boundaries based on the anchor tile
        max_col_boundary = page_origin_col + NUMBER_COLUMNS - 1
        max_row_boundary = page_origin_row + NUMBER_ROWS - 1
        
        current_page_actual_tiles = []
        
        # Iterate through all potential tiles within the page boundaries
        for c in range(page_origin_col, max_col_boundary + 1):
            for r in range(page_origin_row, max_row_boundary + 1):
                tile_in_grid = (c, r)
                if tile_in_grid in all_track_tiles_set and tile_in_grid not in globally_processed_track_tiles:
                    current_page_actual_tiles.append(tile_in_grid)
                    globally_processed_track_tiles.add(tile_in_grid)
        
        if current_page_actual_tiles: # If the page captured any new track tiles
            pages.append(current_page_actual_tiles)
            
    return pages




def get_first_tile_page (page):
    # Sort the data by row (the first element of the tuple) and then by column (the second element of the tuple)
    smallest_row = sorted(page, key=lambda x: (x[0]))[0][0]
    smallest_col = sorted(page, key=lambda x: (x[1]))[0][1]
    return smallest_row,smallest_col

def fill_page (corner_tile,NUMBER_ROWS,NUMBER_COLUMNS):
    col, row = corner_tile
    page = [[(0,0)] * NUMBER_ROWS for _ in range(NUMBER_COLUMNS)]
    for i in range(NUMBER_COLUMNS):
        for j in range(NUMBER_ROWS):
            page[i][j]=(col+i,row+j)
    return page             


def get_filled_pages(ordered_unique_track_tiles, all_track_tiles_set, max_col, max_row):
    filled_pages = []

    NUMBER_COLUMNS = max_col
    NUMBER_ROWS = max_row
    # Update the call to put_tiles_in_pages with the new signature
    pages = put_tiles_in_pages(ordered_unique_track_tiles, all_track_tiles_set, NUMBER_ROWS, NUMBER_COLUMNS)

    for page in pages : # page here is a list of actual tiles for this page
        if not page: # Check if the page (list of tiles) is empty
            continue
        corner_tile = get_first_tile_page(page)
        filled_page = fill_page(corner_tile,NUMBER_ROWS,NUMBER_COLUMNS)
        filled_pages.append(filled_page)

    return filled_pages




