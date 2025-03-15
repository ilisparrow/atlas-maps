

import math

def put_tiles_in_pages (tiles,NUMBER_ROWS,NUMBER_COLUMNS):
    full_processed_list =  []
    pages=[]
    for tile_of_ref in tiles : 
        if tile_of_ref not in full_processed_list:
            min_row = tile_of_ref[1]
            min_col = tile_of_ref[0]
            page_one = []
            for idx, tile in enumerate(tiles) : 
                if tile not in full_processed_list:
                    delta_x = min_row-tile[1]
                    delta_y = min_col-tile[0]
                    if(abs(delta_y)<NUMBER_ROWS and abs(delta_x)<NUMBER_COLUMNS):
                        page_one.append(tile)
                        full_processed_list.append(tile)
                        min_col = tile[0] if tile[0]<min_col else min_col
                        min_row = tile[1] if tile[1]<min_row else min_row
                    else :
                        pass
            pages.append(page_one)
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


def get_filled_pages(tiles,max_col,max_row):
    filled_pages = []

    NUMBER_COLUMNS = max_col
    NUMBER_ROWS = max_row
    pages = put_tiles_in_pages (tiles,NUMBER_ROWS,NUMBER_COLUMNS)

    for page in pages :
        corner_tile = get_first_tile_page(page)
        filled_page = fill_page(corner_tile,NUMBER_ROWS,NUMBER_COLUMNS)
        filled_pages.append(filled_page)

    return filled_pages




