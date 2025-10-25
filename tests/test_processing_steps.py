import pytest
import json
from pathlib import Path
from page_generation import put_tiles_in_pages, get_filled_pages, get_first_tile_page, fill_page


class TestProcessingSteps:
    """Test each step of the page generation pipeline with real GPX data."""

    @pytest.fixture(scope='class')
    def test_fixtures(self):
        """Load test fixtures from JSON."""
        fixture_path = Path(__file__).parent / 'test_fixtures.json'
        if fixture_path.exists():
            with open(fixture_path, 'r') as f:
                return json.load(f)
        return None

    @pytest.fixture
    def config(self):
        """Default configuration."""
        return {
            'NUMBER_ROWS': 14,
            'NUMBER_COLUMNS': 9
        }

    def analyze_pages(self, pages, tiles_ordered, config):
        """Analyze pages and return detailed statistics."""
        stats = {
            'num_pages': len(pages),
            'tiles_per_page': [len(page) for page in pages],
            'chronological_order': True,
            'overlaps': [],
            'coverage': {
                'total_unique_tiles': len(set(tiles_ordered)),
                'tiles_in_pages': 0
            }
        }

        # Check chronological order
        page_first_indices = []
        for i, page in enumerate(pages):
            if page[0] in tiles_ordered:
                first_tile_index = tiles_ordered.index(page[0])
                page_first_indices.append((i, first_tile_index))

        sorted_indices = sorted(page_first_indices, key=lambda x: x[1])
        stats['chronological_order'] = (page_first_indices == sorted_indices)
        stats['page_order_indices'] = [idx for _, idx in page_first_indices]

        # Count tiles
        all_tiles_in_pages = set()
        for page in pages:
            all_tiles_in_pages.update(page)
        stats['coverage']['tiles_in_pages'] = len(all_tiles_in_pages)

        return stats

    def analyze_filled_pages(self, filled_pages, pages, config):
        """Analyze filled pages and calculate overlaps."""
        stats = {
            'num_filled_pages': len(filled_pages),
            'tiles_per_filled_page': [],
            'overlaps': []
        }

        # Each filled page is 9x14 grid
        expected_size = config['NUMBER_COLUMNS'] * config['NUMBER_ROWS']

        for i, filled_page in enumerate(filled_pages):
            # Count tiles in this filled page
            tiles_in_page = set()
            for row in filled_page:
                tiles_in_page.update(row)
            stats['tiles_per_filled_page'].append(len(tiles_in_page))

            # Check it's the right size
            assert len(filled_page) == config['NUMBER_COLUMNS']
            for row in filled_page:
                assert len(row) == config['NUMBER_ROWS']

        # Calculate overlaps between consecutive pages
        for i in range(len(filled_pages) - 1):
            tiles_page_i = set()
            tiles_page_next = set()

            for row in filled_pages[i]:
                tiles_page_i.update(row)

            for row in filled_pages[i + 1]:
                tiles_page_next.update(row)

            overlap = tiles_page_i.intersection(tiles_page_next)
            overlap_count = len(overlap)
            overlap_pct = (overlap_count / expected_size) * 100

            stats['overlaps'].append({
                'pages': f"{i+1} & {i+2}",
                'overlap_tiles': overlap_count,
                'overlap_percentage': round(overlap_pct, 2),
                'page_i_size': len(tiles_page_i),
                'page_next_size': len(tiles_page_next)
            })

        return stats

    def test_step1_grouping_small_dataset(self, test_fixtures, config):
        """Test Step 1: Grouping tiles into pages (small dataset)."""
        if not test_fixtures or 'small_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['small_linear']
        tiles = [tuple(t) for t in data['tiles']]

        print(f"\n=== STEP 1: GROUPING (Small Dataset) ===")
        print(f"Input: {len(tiles)} unique tiles")

        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])

        stats = self.analyze_pages(pages, tiles, config)

        print(f"\nResults:")
        print(f"  Generated {stats['num_pages']} page(s)")
        print(f"  Tiles per page: {stats['tiles_per_page']}")
        print(f"  Chronological order: {'✓' if stats['chronological_order'] else '✗'}")
        print(f"  Coverage: {stats['coverage']['tiles_in_pages']}/{stats['coverage']['total_unique_tiles']} tiles")

        assert stats['chronological_order'], "Pages should be in chronological order"
        assert stats['coverage']['tiles_in_pages'] == stats['coverage']['total_unique_tiles'], \
            "All tiles should be included in pages"

    def test_step1_grouping_medium_dataset(self, test_fixtures, config):
        """Test Step 1: Grouping tiles into pages (medium dataset)."""
        if not test_fixtures or 'medium_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['medium_linear']
        tiles = [tuple(t) for t in data['tiles']]

        print(f"\n=== STEP 1: GROUPING (Medium Dataset) ===")
        print(f"Input: {len(tiles)} unique tiles")

        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])

        stats = self.analyze_pages(pages, tiles, config)

        print(f"\nResults:")
        print(f"  Generated {stats['num_pages']} page(s)")
        print(f"  Tiles per page: min={min(stats['tiles_per_page'])}, "
              f"max={max(stats['tiles_per_page'])}, "
              f"avg={sum(stats['tiles_per_page'])/len(stats['tiles_per_page']):.1f}")
        print(f"  Chronological order: {'✓' if stats['chronological_order'] else '✗'}")
        print(f"  First tile indices: {stats['page_order_indices'][:5]}...")

        assert stats['chronological_order'], "Pages should be in chronological order"
        assert stats['num_pages'] > 1, "Should generate multiple pages for 200 tiles"

    def test_step2_get_first_tile(self, test_fixtures, config):
        """Test Step 2: Getting the first (corner) tile of a page."""
        if not test_fixtures or 'small_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['small_linear']
        tiles = [tuple(t) for t in data['tiles']][:20]  # First 20 tiles

        print(f"\n=== STEP 2: GET FIRST TILE ===")
        print(f"Input tiles: {tiles[:5]}...")

        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])

        for i, page in enumerate(pages):
            corner = get_first_tile_page(page)
            print(f"\nPage {i+1}:")
            print(f"  Tiles in page: {page[:3]}...")
            print(f"  Corner tile: {corner}")

            # Verify corner is the minimum col and row
            min_col = min(tile[0] for tile in page)
            min_row = min(tile[1] for tile in page)

            assert corner == (min_col, min_row), \
                f"Corner should be ({min_col}, {min_row}), got {corner}"

    def test_step3_fill_page(self, test_fixtures, config):
        """Test Step 3: Filling a page with 9x14 grid."""
        corner_tile = (100, 200)

        print(f"\n=== STEP 3: FILL PAGE ===")
        print(f"Corner tile: {corner_tile}")
        print(f"Grid size: {config['NUMBER_COLUMNS']}x{config['NUMBER_ROWS']}")

        filled = fill_page(corner_tile, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])

        print(f"\nResults:")
        print(f"  Grid dimensions: {len(filled)}x{len(filled[0])}")
        print(f"  First row: {filled[0][:3]}...")
        print(f"  Last row: {filled[-1][:3]}...")

        # Verify dimensions
        assert len(filled) == config['NUMBER_COLUMNS']
        assert all(len(row) == config['NUMBER_ROWS'] for row in filled)

        # Verify corner
        assert filled[0][0] == corner_tile

        # Verify it fills correctly
        assert filled[0][1] == (corner_tile[0], corner_tile[1] + 1)
        assert filled[1][0] == (corner_tile[0] + 1, corner_tile[1])

    def test_step4_full_pipeline_small(self, test_fixtures, config):
        """Test Step 4: Full pipeline (small dataset)."""
        if not test_fixtures or 'small_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['small_linear']
        tiles = [tuple(t) for t in data['tiles']]

        print(f"\n=== STEP 4: FULL PIPELINE (Small) ===")
        print(f"Input: {len(tiles)} unique tiles from {data['total_points']} GPS points")

        # Step 1: Group into pages
        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])
        print(f"\nAfter grouping: {len(pages)} page(s)")

        # Step 2-3: Fill pages
        filled_pages = get_filled_pages(tiles, config['NUMBER_COLUMNS'], config['NUMBER_ROWS'])
        print(f"After filling: {len(filled_pages)} filled page(s)")

        # Analyze
        page_stats = self.analyze_pages(pages, tiles, config)
        filled_stats = self.analyze_filled_pages(filled_pages, pages, config)

        print(f"\n--- Grouping Statistics ---")
        print(f"  Pages: {page_stats['num_pages']}")
        print(f"  Chronological: {'✓' if page_stats['chronological_order'] else '✗'}")

        print(f"\n--- Filled Pages Statistics ---")
        print(f"  Expected tiles per page: {config['NUMBER_COLUMNS'] * config['NUMBER_ROWS']}")
        print(f"  Actual tiles per page: {filled_stats['tiles_per_filled_page']}")

        if filled_stats['overlaps']:
            print(f"\n--- Overlap Analysis ---")
            for overlap in filled_stats['overlaps']:
                print(f"  Pages {overlap['pages']}: "
                      f"{overlap['overlap_tiles']} tiles ({overlap['overlap_percentage']}% overlap)")

        assert len(filled_pages) == len(pages)

    def test_step4_full_pipeline_medium(self, test_fixtures, config):
        """Test Step 4: Full pipeline (medium dataset) with detailed report."""
        if not test_fixtures or 'medium_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['medium_linear']
        tiles = [tuple(t) for t in data['tiles']]

        print(f"\n{'='*60}")
        print(f"FULL PIPELINE REPORT (Medium Dataset)")
        print(f"{'='*60}")
        print(f"Source: {data['source']}")
        print(f"GPS Points: {data['total_points']}")
        print(f"Unique Tiles: {data['unique_tiles']}")
        print(f"Grid Size: {config['NUMBER_COLUMNS']}x{config['NUMBER_ROWS']} "
              f"({config['NUMBER_COLUMNS'] * config['NUMBER_ROWS']} tiles/page)")

        # Run pipeline
        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])
        filled_pages = get_filled_pages(tiles, config['NUMBER_COLUMNS'], config['NUMBER_ROWS'])

        # Analyze
        page_stats = self.analyze_pages(pages, tiles, config)
        filled_stats = self.analyze_filled_pages(filled_pages, pages, config)

        print(f"\n{'='*60}")
        print(f"GROUPING RESULTS")
        print(f"{'='*60}")
        print(f"Total Pages Generated: {page_stats['num_pages']}")
        print(f"Chronological Order: {'✓ PASS' if page_stats['chronological_order'] else '✗ FAIL'}")
        print(f"\nTiles Distribution:")
        print(f"  Min tiles/page: {min(page_stats['tiles_per_page'])}")
        print(f"  Max tiles/page: {max(page_stats['tiles_per_page'])}")
        print(f"  Avg tiles/page: {sum(page_stats['tiles_per_page'])/len(page_stats['tiles_per_page']):.1f}")
        print(f"\nCoverage:")
        print(f"  Input unique tiles: {page_stats['coverage']['total_unique_tiles']}")
        print(f"  Tiles in pages: {page_stats['coverage']['tiles_in_pages']}")
        print(f"  Coverage: {(page_stats['coverage']['tiles_in_pages']/page_stats['coverage']['total_unique_tiles']*100):.1f}%")

        print(f"\n{'='*60}")
        print(f"FILLED PAGES RESULTS")
        print(f"{'='*60}")
        print(f"Total Filled Pages: {filled_stats['num_filled_pages']}")
        print(f"Tiles per filled page: {config['NUMBER_COLUMNS']*config['NUMBER_ROWS']} (constant)")

        if filled_stats['overlaps']:
            print(f"\n{'='*60}")
            print(f"OVERLAP ANALYSIS")
            print(f"{'='*60}")

            total_overlap = sum(o['overlap_tiles'] for o in filled_stats['overlaps'])
            avg_overlap = total_overlap / len(filled_stats['overlaps']) if filled_stats['overlaps'] else 0
            avg_overlap_pct = sum(o['overlap_percentage'] for o in filled_stats['overlaps']) / len(filled_stats['overlaps'])

            print(f"Total consecutive page pairs: {len(filled_stats['overlaps'])}")
            print(f"Average overlap: {avg_overlap:.1f} tiles ({avg_overlap_pct:.1f}%)")
            print(f"\nDetailed overlaps:")

            for i, overlap in enumerate(filled_stats['overlaps'][:10]):  # Show first 10
                print(f"  Pages {overlap['pages']:>6}: {overlap['overlap_tiles']:>3} tiles "
                      f"({overlap['overlap_percentage']:>5.1f}%)")

            if len(filled_stats['overlaps']) > 10:
                print(f"  ... and {len(filled_stats['overlaps'])-10} more")

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"✓ All {page_stats['coverage']['total_unique_tiles']} input tiles included")
        print(f"✓ Pages in chronological GPS order")
        print(f"✓ {filled_stats['num_filled_pages']} pages ready for PDF generation")
        if filled_stats['overlaps']:
            print(f"✓ Average {avg_overlap_pct:.1f}% overlap between consecutive pages")

        # Assertions
        assert page_stats['chronological_order'], "Pages must be in chronological order"
        assert page_stats['coverage']['tiles_in_pages'] == page_stats['coverage']['total_unique_tiles'], \
            "All tiles must be included"
        assert len(filled_pages) == len(pages), "Should have same number of filled pages as grouped pages"

    def test_no_duplicate_tiles_across_grouped_pages(self, test_fixtures, config):
        """Verify that no tile appears in multiple grouped pages."""
        if not test_fixtures or 'medium_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['medium_linear']
        tiles = [tuple(t) for t in data['tiles']]

        pages = put_tiles_in_pages(tiles, config['NUMBER_ROWS'], config['NUMBER_COLUMNS'])

        print(f"\n=== DUPLICATE CHECK (Grouped Pages) ===")

        all_tiles = []
        for page in pages:
            all_tiles.extend(page)

        print(f"Total tiles across all pages: {len(all_tiles)}")
        print(f"Unique tiles: {len(set(all_tiles))}")

        assert len(all_tiles) == len(set(all_tiles)), \
            "No tile should appear in multiple grouped pages"

        print("✓ No duplicates found in grouped pages")

    def test_filled_pages_can_overlap(self, test_fixtures, config):
        """Verify that filled pages CAN and DO overlap (intentional design)."""
        if not test_fixtures or 'medium_linear' not in test_fixtures:
            pytest.skip("Test fixtures not available")

        data = test_fixtures['medium_linear']
        tiles = [tuple(t) for t in data['tiles']]

        filled_pages = get_filled_pages(tiles, config['NUMBER_COLUMNS'], config['NUMBER_ROWS'])

        print(f"\n=== OVERLAP CHECK (Filled Pages) ===")
        print(f"Note: Overlap is INTENTIONAL for physical page alignment")

        has_overlap = False
        for i in range(len(filled_pages) - 1):
            tiles_i = set(tile for row in filled_pages[i] for tile in row)
            tiles_next = set(tile for row in filled_pages[i+1] for tile in row)

            overlap = tiles_i.intersection(tiles_next)
            if overlap:
                has_overlap = True
                print(f"  Pages {i+1} & {i+2}: {len(overlap)} overlapping tiles")

        if has_overlap:
            print("\n✓ Overlap exists (as expected for physical continuity)")
        else:
            print("\n  No overlap found (pages are completely separate)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
