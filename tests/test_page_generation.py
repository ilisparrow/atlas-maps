import pytest
from page_generation import put_tiles_in_pages, get_filled_pages, get_first_tile_page, fill_page


class TestPageGeneration:
    """Test page generation algorithm with various GPX track patterns."""

    def test_small_loop_single_page(self):
        """Test 1: Small loop that fits in one page."""
        # Simulate a small square loop
        tiles = [(5, 5), (5, 6), (6, 6), (6, 5), (5, 5)]  # Returns to start
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        assert len(pages) == 1, f"Expected 1 page, got {len(pages)}"
        assert len(pages[0]) == 4, f"Expected 4 unique tiles, got {len(pages[0])}"

    def test_west_to_east_multiple_pages(self):
        """Test 2: Track going west to east over multiple pages."""
        # delta_y = min_col - tile[0], checked against NUMBER_ROWS (14)
        # So tiles need to span more than 14 in column direction
        tiles = [(0, 5), (5, 5), (10, 5), (15, 5), (20, 5), (25, 5), (30, 5)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        # Check that pages are generated in chronological order
        # First page should contain early tiles, not late ones
        assert len(pages) > 1, f"Expected multiple pages, got {len(pages)}"

        # First page should start with first tile
        assert (0, 5) in pages[0], "First page should contain the first tile"

        # Verify pages follow sequential order (first tile of each page)
        first_tiles_cols = [min(tile[0] for tile in page) for page in pages]
        assert first_tiles_cols == sorted(first_tiles_cols), \
            f"Pages out of order! First tile columns: {first_tiles_cols}"

    def test_east_to_west_reverse(self):
        """Test 3: Track going east to west (reverse direction)."""
        # Tiles spanning more than 9 columns to force multiple pages
        tiles = [(50, 5), (40, 5), (30, 5), (20, 5), (10, 5), (0, 5)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        assert len(pages) > 1, f"Expected multiple pages, got {len(pages)}"

        # First page should contain the first chronological tile (50, 5)
        assert (50, 5) in pages[0], "First page should contain the first chronological tile"

        # Pages should follow the track direction (decreasing columns)
        first_tiles_cols = [min(tile[0] for tile in page) for page in pages]
        # Since we go east to west, later pages should have smaller column numbers
        assert pages[0][0][0] > pages[-1][0][0], \
            f"Expected decreasing column progression, got {first_tiles_cols}"

    def test_north_to_south(self):
        """Test 4: Track going north to south."""
        # delta_x = min_row - tile[1], checked against NUMBER_COLUMNS (9)
        # So tiles need to span more than 9 in row direction
        tiles = [(5, 0), (5, 5), (5, 10), (5, 15), (5, 20)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        assert len(pages) > 1, f"Expected multiple pages, got {len(pages)}"
        assert (5, 0) in pages[0], "First page should contain the first tile"

        # Check sequential order by row
        first_tiles_rows = [min(tile[1] for tile in page) for page in pages]
        assert first_tiles_rows == sorted(first_tiles_rows), \
            f"Pages out of order! First tile rows: {first_tiles_rows}"

    def test_south_to_north(self):
        """Test 5: Track going south to north (reverse)."""
        # delta_x = min_row - tile[1], checked against NUMBER_COLUMNS (9)
        # So tiles need to span more than 9 in row direction
        tiles = [(5, 20), (5, 15), (5, 10), (5, 5), (5, 0)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        assert len(pages) > 1, f"Expected multiple pages, got {len(pages)}"
        assert (5, 20) in pages[0], "First page should contain the first chronological tile"

    def test_big_loop_with_tiny_detour(self):
        """Test 6: Big loop with a small detour to a distant tile."""
        # Main loop around (10, 10) area
        main_loop = [(10, 10), (11, 10), (12, 10), (12, 11), (12, 12),
                     (11, 12), (10, 12), (10, 11)]
        # Tiny detour to distant location
        detour = [(50, 50)]
        # Back to main area
        back = [(10, 10)]

        tiles = main_loop + detour + back
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        # Main loop should be on first page
        for tile in main_loop:
            assert tile in pages[0], f"Main loop tile {tile} should be on first page"

        # The detour tile should be on a separate page (can't fit with main loop)
        detour_page_idx = None
        for idx, page in enumerate(pages):
            if (50, 50) in page:
                detour_page_idx = idx
                break

        assert detour_page_idx is not None, "Detour tile should be in some page"
        # In chronological order, detour should appear after main loop
        assert detour_page_idx > 0, "Detour should not be on first page"

    def test_no_duplicate_tiles_in_pages(self):
        """Test 7: Ensure tiles don't appear in multiple pages."""
        tiles = [(0, 5), (5, 5), (10, 5), (15, 5), (20, 5)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        # Collect all tiles across all pages
        all_tiles = []
        for page in pages:
            all_tiles.extend(page)

        # Check for duplicates
        assert len(all_tiles) == len(set(all_tiles)), \
            "Tiles should not appear in multiple pages"

    def test_all_tiles_included(self):
        """Test that all unique tiles are included in some page."""
        tiles = [(0, 5), (5, 5), (10, 5), (5, 5), (15, 5), (0, 5)]  # Has duplicates
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        unique_input_tiles = set(tiles)
        all_output_tiles = set()
        for page in pages:
            all_output_tiles.update(page)

        assert unique_input_tiles == all_output_tiles, \
            "All unique input tiles should appear in output pages"

    def test_filled_pages_creates_full_grids(self):
        """Test that fill_page creates proper 9x14 grids."""
        tiles = [(10, 20), (11, 20), (12, 21)]
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        filled_pages = get_filled_pages(tiles, NUMBER_COLUMNS, NUMBER_ROWS)

        # Each filled page should be a 9x14 grid
        for page in filled_pages:
            assert len(page) == NUMBER_COLUMNS, \
                f"Expected {NUMBER_COLUMNS} columns, got {len(page)}"
            for row in page:
                assert len(row) == NUMBER_ROWS, \
                    f"Expected {NUMBER_ROWS} rows, got {len(row)}"

    def test_chronological_order_with_revisited_area(self):
        """Test that revisiting an area doesn't break chronological page order."""
        # Go to area A, then area B (far), then back to area A
        area_a_first = [(5, 5), (6, 5), (7, 5)]
        area_b = [(30, 30), (31, 30), (32, 30)]
        area_a_second = [(8, 5), (9, 5)]

        tiles = area_a_first + area_b + area_a_second
        NUMBER_ROWS = 14
        NUMBER_COLUMNS = 9

        pages = put_tiles_in_pages(tiles, NUMBER_ROWS, NUMBER_COLUMNS)

        # All area A tiles should be on same page (they're close)
        area_a_tiles = set(area_a_first + area_a_second)
        area_a_page = None
        for idx, page in enumerate(pages):
            if (5, 5) in page:
                area_a_page = idx
                # Check all area A tiles are on this page
                for tile in area_a_tiles:
                    assert tile in page, \
                        f"Tile {tile} should be with other area A tiles on page {idx}"
                break

        # Area B should be on a different page
        area_b_page = None
        for idx, page in enumerate(pages):
            if (30, 30) in page:
                area_b_page = idx
                break

        assert area_a_page != area_b_page, "Area A and B should be on different pages"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
