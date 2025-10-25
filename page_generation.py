
import math
import os

# Try to load dotenv if available (for production), but don't fail if missing (for tests)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get configuration from environment
DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "false").lower() == "true"

def debug_print(message):
    """Print debug messages only if DEBUG_LOGGING is enabled"""
    if DEBUG_LOGGING:
        print(message, flush=True)

def put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS):
    """
    Group tiles into pages.

    Args:
        tiles: List of (col, row) tile coordinates in chronological order
        NUMBER_ROWS: Number of rows per page (typically 14)
        NUMBER_COLUMNS: Number of columns per page (typically 9)
    """
    debug_print(f"[DEBUG put_tiles_in_pages] INPUT: {len(tiles)} tiles, NUMBER_ROWS={NUMBER_ROWS}, NUMBER_COLUMNS={NUMBER_COLUMNS}")
    debug_print(f"[DEBUG put_tiles_in_pages] First 5 tiles: {tiles[:5]}")

    full_processed_list = []
    pages = []

    for tile_of_ref in tiles:
        if tile_of_ref not in full_processed_list:
            # Track the extent of the current page
            min_row = tile_of_ref[1]
            min_col = tile_of_ref[0]
            max_row = tile_of_ref[1]
            max_col = tile_of_ref[0]
            page_one = []

            for idx, tile in enumerate(tiles):
                if tile not in full_processed_list:
                    # Calculate what the new extent would be if we add this tile
                    new_min_row = min(min_row, tile[1])
                    new_max_row = max(max_row, tile[1])
                    new_min_col = min(min_col, tile[0])
                    new_max_col = max(max_col, tile[0])

                    # Check if the total span would exceed the page limits
                    row_span = new_max_row - new_min_row
                    col_span = new_max_col - new_min_col

                    if (col_span < NUMBER_COLUMNS and row_span < NUMBER_ROWS):
                        page_one.append(tile)
                        full_processed_list.append(tile)
                        # Update the extent to include this tile
                        min_row = new_min_row
                        max_row = new_max_row
                        min_col = new_min_col
                        max_col = new_max_col

            pages.append(page_one)

    debug_print(f"[DEBUG put_tiles_in_pages] OUTPUT: {len(pages)} pages, tiles per page: {[len(p) for p in pages]}")
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


def get_filled_pages(tiles, max_col, max_row):
    debug_print(f"[DEBUG get_filled_pages] INPUT: {len(tiles)} tiles, max_col={max_col}, max_row={max_row}")
    filled_pages = []

    NUMBER_COLUMNS = max_col
    NUMBER_ROWS = max_row
    debug_print(f"[DEBUG get_filled_pages] Calling put_tiles_in_pages with NUMBER_ROWS={NUMBER_ROWS}, NUMBER_COLUMNS={NUMBER_COLUMNS}")
    pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

    for page in pages:
        corner_tile = get_first_tile_page(page)
        filled_page = fill_page(corner_tile, NUMBER_ROWS, NUMBER_COLUMNS)
        filled_pages.append(filled_page)

    debug_print(f"[DEBUG get_filled_pages] OUTPUT: {len(filled_pages)} filled pages")
    return filled_pages




