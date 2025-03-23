import math

def put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS):
    processed_tiles = set()
    pages = []
    
    for tile in tiles:
        if tile in processed_tiles:
            continue
        
        # Create a new page with this tile as a reference
        ref_col, ref_row = tile
        
        # Try different positions for the page to maximize coverage of unprocessed tiles
        best_corner = (ref_col, ref_row)
        best_coverage = 0
        
        for col_offset in range(-NUMBER_COLUMNS + 1, 1):
            for row_offset in range(-NUMBER_ROWS + 1, 1):
                min_col = ref_col + col_offset
                min_row = ref_row + row_offset
                max_col = min_col + NUMBER_COLUMNS - 1
                max_row = min_row + NUMBER_ROWS - 1
                
                # Count how many unprocessed tiles would be covered
                coverage = sum(1 for t in tiles if t not in processed_tiles and 
                              min_col <= t[0] <= max_col and min_row <= t[1] <= max_row)
                
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_corner = (min_col, min_row)
        
        # Create a page with the best corner
        min_col, min_row = best_corner
        max_col = min_col + NUMBER_COLUMNS - 1
        max_row = min_row + NUMBER_ROWS - 1
        
        # Add all tiles within this page
        page_tiles = []
        for t in tiles:
            col, row = t
            if min_col <= col <= max_col and min_row <= row <= max_row:
                page_tiles.append(t)
                if t not in processed_tiles:
                    processed_tiles.add(t)
        
        pages.append(page_tiles)
    
    return pages

def get_first_tile_page(page):
    # Find the smallest column and row (top-left corner)
    smallest_col = min(tile[0] for tile in page)
    smallest_row = min(tile[1] for tile in page)
    return smallest_col, smallest_row

def fill_page(corner_tile, NUMBER_ROWS, NUMBER_COLUMNS):
    col, row = corner_tile
    page = [[(0, 0)] * NUMBER_ROWS for _ in range(NUMBER_COLUMNS)]
    for i in range(NUMBER_COLUMNS):
        for j in range(NUMBER_ROWS):
            page[i][j] = (col + i, row + j)
    return page             

def get_filled_pages(tiles, max_col, max_row):
    filled_pages = []
    NUMBER_COLUMNS = max_col
    NUMBER_ROWS = max_row
    pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)
    for page in pages:
        corner_tile = get_first_tile_page(page)
        filled_page = fill_page(corner_tile, NUMBER_ROWS, NUMBER_COLUMNS)
        filled_pages.append(filled_page)
    return filled_pages