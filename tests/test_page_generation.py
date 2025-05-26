import unittest
from page_generation import put_tiles_in_pages, get_first_tile_page, fill_page, get_filled_pages

class TestPageGenerationUtils(unittest.TestCase):
    def assertListOfPagesEqual(self, list1, list2, msg=None):
        """
        Helper to compare lists of pages. Each page is a list of tiles (tuples).
        Sorts tiles within each page, then compares the list of pages (order of pages matters).
        """
        normalized1 = [sorted(page) for page in list1]
        normalized2 = [sorted(page) for page in list2]
        self.assertEqual(normalized1, normalized2, msg)

class TestPutTilesInPages(TestPageGenerationUtils):
    def test_empty_tiles_list(self):
        self.assertEqual(put_tiles_in_pages([], set(), NUMBER_ROWS=2, NUMBER_COLUMNS=2), [])

    def test_single_tile(self):
        ordered = [(0,0)]
        all_tiles = {(0,0)}
        expected = [[(0,0)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)

    def test_simple_page_from_ordered_track(self):
        # All tiles fit in one page defined by the first tile in ordered_unique_track_tiles
        ordered = [(0,0), (0,1), (1,0)]
        all_tiles = {(0,0), (0,1), (1,0), (5,5)} # (5,5) is outside this page
        # Page starts at (0,0). Max_col=1, Max_row=1 for a 2x2 page.
        # Tiles collected: (0,0), (0,1), (1,0)
        expected = [[(0,0), (0,1), (1,0)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)

    def test_multiple_pages_no_overlap_track_order(self):
        ordered = [(0,0), (5,5)] # Track determines page anchor order
        all_tiles = {(0,0), (0,1), (5,5), (5,6)}
        # Page 1 from (0,0): [(0,0), (0,1)]
        # Page 2 from (5,5) (since (0,0), (0,1) are processed): [(5,5), (5,6)]
        expected = [[(0,0), (0,1)], [(5,5), (5,6)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)

    def test_tiles_form_larger_page_than_dims_track_order(self):
        ordered = [(0,0), (0,2)] # Anchors based on track order
        all_tiles = {(0,0), (0,1), (1,0), (1,1), (0,2), (1,2)} # Forms a 2x3 area
        # Page R=2, C=2
        # 1. Anchor (0,0). Page tiles: (0,0), (0,1), (1,0), (1,1). Processed: {(0,0),(0,1),(1,0),(1,1)}
        # 2. Anchor (0,2) (next in ordered). Page tiles: (0,2), (1,2). Processed: {all}
        expected = [[(0,0), (0,1), (1,0), (1,1)], [(0,2), (1,2)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)
        
    def test_scattered_tiles_multiple_pages_track_order(self):
        ordered = [(0,0), (0,5), (5,0), (5,5)] # Track order defines anchors
        all_tiles = {(0,0), (0,5), (5,0), (5,5)}
        # Page R=3, C=3
        # 1. Anchor (0,0). Page tiles: [(0,0)]. Processed: {(0,0)}
        # 2. Anchor (0,5). Page tiles: [(0,5)]. Processed: {(0,0), (0,5)}
        # 3. Anchor (5,0). Page tiles: [(5,0)]. Processed: {(0,0), (0,5), (5,0)}
        # 4. Anchor (5,5). Page tiles: [(5,5)]. Processed: {all}
        expected = [[(0,0)], [(0,5)], [(5,0)], [(5,5)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=3, NUMBER_COLUMNS=3), expected)

    def test_duplicate_tiles_in_all_tiles_set(self):
        # ordered_unique_track_tiles is by definition unique. all_track_tiles_set is a set.
        # This test ensures that if all_track_tiles_set somehow got non-unique inputs (which set handles), it's fine.
        # More importantly, it tests that an anchor is not re-processed.
        ordered = [(0,0), (0,1)]
        all_tiles = {(0,0), (0,0), (0,1)} 
        # Page R=2, C=2
        # 1. Anchor (0,0). Page: [(0,0), (0,1)]. Processed: {(0,0), (0,1)}
        # 2. Anchor (0,1) is in ordered, but already processed. Skip.
        expected = [[(0,0), (0,1)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)

    def test_left_to_right_sequence(self):
        ordered = [(0,0), (1,0), (2,0)]
        all_tiles = {(0,0), (1,0), (2,0)}
        # C=1, R=1 (each tile is its own page)
        # 1. Anchor (0,0). Page: [(0,0)]. Processed: {(0,0)}
        # 2. Anchor (1,0). Page: [(1,0)]. Processed: {(0,0), (1,0)}
        # 3. Anchor (2,0). Page: [(2,0)]. Processed: {(0,0), (1,0), (2,0)}
        expected = [[(0,0)], [(1,0)], [(2,0)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=1, NUMBER_COLUMNS=1), expected)

    def test_right_to_left_sequence(self):
        ordered = [(2,0), (1,0), (0,0)]
        all_tiles = {(2,0), (1,0), (0,0)}
        # C=1, R=1
        # 1. Anchor (2,0). Page: [(2,0)]. Processed: {(2,0)}
        # 2. Anchor (1,0). Page: [(1,0)]. Processed: {(2,0), (1,0)}
        # 3. Anchor (0,0). Page: [(0,0)]. Processed: {(2,0), (1,0), (0,0)}
        expected = [[(2,0)], [(1,0)], [(0,0)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=1, NUMBER_COLUMNS=1), expected)

    def test_loop_sequence(self):
        ordered = [(0,0), (1,0), (1,1), (0,1)] # (0,0) is not repeated for unique list
        all_tiles = {(0,0), (1,0), (1,1), (0,1)}
        # C=2,R=2. Page dimensions 2x2. Anchor (0,0)
        # Max_col=1, Max_row=1.
        # Page tiles: (0,0), (1,0), (0,1), (1,1) - order within page doesn't matter due to helper.
        expected = [[(0,0), (0,1), (1,0), (1,1)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)
        
    def test_track_smaller_than_page_dims(self):
        ordered = [(0,0), (0,1)]
        all_tiles = {(0,0), (0,1)}
        # C=3,R=3. Page dimensions 3x3. Anchor (0,0)
        # Max_col=2, Max_row=2.
        # Page tiles: (0,0), (0,1)
        expected = [[(0,0), (0,1)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=3, NUMBER_COLUMNS=3), expected)

    def test_page_content_collection(self):
        # Ensures pages collect all relevant track tiles from all_track_tiles_set
        # and tiles are not duplicated across pages due to globally_processed_track_tiles.
        ordered = [(0,0), (0,2)] # Anchors
        all_tiles = {(0,0), (0,1), (1,0), (1,1), (0,2), (1,2), (0,3), (1,3)}
        # Page R=2, C=2
        # 1. Anchor (0,0). Page grid [0,0] to [1,1]. Tiles collected: (0,0), (0,1), (1,0), (1,1).
        #    Globally processed: {(0,0), (0,1), (1,0), (1,1)}.
        # 2. Anchor (0,2). Page grid [0,2] to [1,3]. Tiles collected: (0,2), (1,2), (0,3), (1,3).
        #    (0,1) is not re-added even if it were in range for anchor (0,2)'s page grid.
        expected = [[(0,0), (0,1), (1,0), (1,1)], [(0,2), (0,3), (1,2), (1,3)]]
        actual_pages = put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2)
        self.assertListOfPagesEqual(actual_pages, expected)
        
    def test_anchor_already_processed(self):
        # Anchor (0,1) is part of the first page from anchor (0,0)
        # So when (0,1) comes up as an anchor, it should be skipped.
        ordered = [(0,0), (0,1), (0,2)] 
        all_tiles = {(0,0), (0,1), (1,0), (1,1), (0,2), (1,2)}
        # Page R=2, C=2
        # 1. Anchor (0,0). Page tiles: (0,0), (0,1), (1,0), (1,1). 
        #    Globally processed: {(0,0),(0,1),(1,0),(1,1)}.
        # 2. Anchor (0,1) is in ordered. Is (0,1) in globally_processed? Yes. Skip.
        # 3. Anchor (0,2). Page tiles: (0,2), (1,2).
        expected = [[(0,0), (0,1), (1,0), (1,1)], [(0,2), (1,2)]]
        self.assertListOfPagesEqual(put_tiles_in_pages(ordered, all_tiles, NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)


class TestGetFirstTilePage(unittest.TestCase): # No changes expected
    def test_basic_case(self):
        self.assertEqual(get_first_tile_page(page=[(1,2), (0,1), (3,4)]), (0,1))
        self.assertEqual(get_first_tile_page(page=[(1,2), (0,1), (3,0)]), (0,0))

    def test_single_tile_page(self):
        self.assertEqual(get_first_tile_page(page=[(5,5)]), (5,5))

class TestFillPage(unittest.TestCase): # No changes expected
    def test_basic_fill(self):
        expected = [[(0,0),(0,1)], [(1,0),(1,1)]]
        self.assertEqual(fill_page(corner_tile=(0,0), NUMBER_ROWS=2, NUMBER_COLUMNS=2), expected)

    def test_offset_fill(self):
        expected = [[(1,1)]]
        self.assertEqual(fill_page(corner_tile=(1,1), NUMBER_ROWS=1, NUMBER_COLUMNS=1), expected)

    def test_3x2_fill(self):
        expected = [[(0,0),(0,1)], [(1,0),(1,1)], [(2,0),(2,1)]]
        self.assertEqual(fill_page(corner_tile=(0,0), NUMBER_ROWS=2, NUMBER_COLUMNS=3), expected)

class TestGetFilledPages(TestPageGenerationUtils):
    def test_integration_empty(self):
        self.assertEqual(get_filled_pages(ordered_unique_track_tiles=[], all_track_tiles_set=set(), max_col=2, max_row=2), [])

    def test_integration_simple(self):
        ordered = [(0,0), (0,1)]
        all_tiles = {(0,0), (0,1)}
        max_col=2
        max_row=2
        # put_tiles_in_pages for ordered=[(0,0),(0,1)], all_tiles={(0,0),(0,1)}, R=2,C=2
        # 1. Anchor (0,0). Page grid [0,0] to [1,1]. Tiles: (0,0), (0,1). Globally processed: {(0,0),(0,1)}
        # 2. Anchor (0,1) is processed. Skip.
        # Resulting pages_of_tiles = [[(0,0), (0,1)]]
        #
        # For this single page_of_tiles [(0,0), (0,1)]:
        #   get_first_tile_page([(0,0),(0,1)]) -> (0,0)
        #   fill_page((0,0), R=2, C=2) -> [[(0,0),(0,1)], [(1,0),(1,1)]]
        expected_filled_pages = [ [[(0,0),(0,1)], [(1,0),(1,1)]] ]
        self.assertEqual(get_filled_pages(ordered, all_tiles, max_col, max_row), expected_filled_pages)

    def test_integration_two_pages_track_order(self):
        ordered = [(0,0), (3,3)] # Track order
        all_tiles = {(0,0), (3,3)}
        max_col=2
        max_row=2
        # put_tiles_in_pages for ordered=[(0,0),(3,3)], all_tiles={(0,0),(3,3)}, R=2,C=2
        # 1. Anchor (0,0). Page grid [0,0] to [1,1]. Tiles: [(0,0)]. Globally processed: {(0,0)}
        # 2. Anchor (3,3). Page grid [3,3] to [4,4]. Tiles: [(3,3)]. Globally processed: {(0,0),(3,3)}
        # Resulting pages_of_tiles = [[(0,0)], [(3,3)]]
        #
        # Page 1: tiles [(0,0)]. Corner (0,0). Fill: page1_fill = [[(0,0),(0,1)],[(1,0),(1,1)]]
        # Page 2: tiles [(3,3)]. Corner (3,3). Fill: page2_fill = [[(3,3),(3,4)],[(4,3),(4,4)]]
        expected_filled_pages = [
            [[(0,0),(0,1)],[(1,0),(1,1)]], # From anchor (0,0)
            [[(3,3),(3,4)],[(4,3),(4,4)]]  # From anchor (3,3)
        ]
        self.assertEqual(get_filled_pages(ordered, all_tiles, max_col, max_row), expected_filled_pages)

    def test_integration_right_to_left(self):
        ordered = [(2,0), (1,0), (0,0)]
        all_tiles = {(2,0), (1,0), (0,0)}
        max_c, max_r = 1, 1
        # put_tiles_in_pages for ordered=[(2,0),(1,0),(0,0)], all_tiles={(2,0),(1,0),(0,0)}, R=1,C=1
        # 1. Anchor (2,0). Page grid [2,0] to [2,0]. Tiles: [(2,0)]. Processed: {(2,0)}
        # 2. Anchor (1,0). Page grid [1,0] to [1,0]. Tiles: [(1,0)]. Processed: {(2,0),(1,0)}
        # 3. Anchor (0,0). Page grid [0,0] to [0,0]. Tiles: [(0,0)]. Processed: {(2,0),(1,0),(0,0)}
        # Resulting pages_of_tiles = [[(2,0)], [(1,0)], [(0,0)]]
        #
        # Filled pages:
        # Page 1 (from (2,0)): [[(2,0)]]
        # Page 2 (from (1,0)): [[(1,0)]]
        # Page 3 (from (0,0)): [[(0,0)]]
        expected_filled_pages = [ [[(2,0)]], [[(1,0)]], [[(0,0)]] ]
        self.assertEqual(get_filled_pages(ordered, all_tiles, max_c, max_r), expected_filled_pages)

    def test_integration_complex_put_tiles_track_order(self):
        ordered = [(0,0), (0,2)] # Track order
        all_tiles = {(0,0), (0,1), (1,0), (1,1), (0,2), (1,2)}
        max_col=2
        max_row=2
        # put_tiles_in_pages result from earlier test: [[(0,0), (0,1), (1,0), (1,1)], [(0,2), (1,2)]]
        #
        # Page 1: tiles [(0,0), (0,1), (1,0), (1,1)]. Corner (0,0).
        # Fill: [[(0,0),(0,1)], [(1,0),(1,1)]]
        page1_fill = [[(0,0),(0,1)], [(1,0),(1,1)]]
        # Page 2: tiles [(0,2), (1,2)]. Corner (0,2).
        # Fill: [[(0,2),(0,3)], [(1,2),(1,3)]]
        page2_fill = [[(0,2),(0,3)], [(1,2),(1,3)]]
        
        expected_filled_pages = [page1_fill, page2_fill]
        self.assertEqual(get_filled_pages(ordered, all_tiles, max_col, max_row), expected_filled_pages)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
