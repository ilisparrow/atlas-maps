# Testing Documentation

This document describes the comprehensive test suite for the GPX to Map page generation system.

## Quick Start

### Run All Tests
```bash
docker build -f Dockerfile.test -t gpx-test .
docker run --rm gpx-test
```

### Generate Analysis Report Only
```bash
docker run --rm gpx-test bash -c "python3 extract_test_data.py && python3 generate_report.py"
```

## Test Structure

### 1. Test Fixtures (`extract_test_data.py`)
Extracts real tile sequences from GPX files as JSON fixtures:
- **small_linear**: 50 tiles (481 GPS points)
- **medium_linear**: 200 tiles (3,248 GPS points)
- **full_viarhona**: 1,070 tiles (18,600 GPS points)
- **mini_map**: 12 tiles (80 GPS points)

### 2. Unit Tests (`tests/test_processing_steps.py`)
Tests each processing step independently:

#### Step 1: Grouping Tiles into Pages
- **Function**: `put_tiles_in_pages()`
- **Tests**:
  - Small dataset grouping
  - Medium dataset grouping
  - Chronological order verification
  - No duplicate tiles across pages

#### Step 2: Finding Corner Tile
- **Function**: `get_first_tile_page()`
- **Tests**: Corner tile calculation (min col, min row)

#### Step 3: Filling Page Grid
- **Function**: `fill_page()`
- **Tests**: 9×14 grid generation from corner tile

#### Step 4: Full Pipeline
- **Functions**: Complete pipeline from tiles → filled pages
- **Tests**:
  - Small dataset end-to-end
  - Medium dataset end-to-end with detailed statistics
  - Overlap analysis (intentional for page continuity)

### 3. Report Generator (`generate_report.py`)
Generates comprehensive analysis reports for all datasets.

## Test Results Summary

### Dataset: ViaRhôna (Full)
- **GPS Points**: 18,600
- **Unique Tiles**: 1,070
- **Pages Generated**: 53
- **Chronological Order**: ✓ YES
- **Average Overlap**: 19.1% (24 tiles between consecutive pages)

### Key Findings
1. ✅ All pages are in **chronological GPS order**
2. ✅ All input tiles are included (100% coverage)
3. ✅ No duplicate tiles in grouped pages
4. ✅ Intentional overlap (avg 19.1%) for physical page continuity
5. ✅ Min overlap: 0% (some pages don't overlap)
6. ✅ Max overlap: 35.7% (some pages overlap significantly)

## What Was Fixed

### Problem
When using `set()` to collect unique tiles, the chronological order from the GPS track was lost. This caused:
- Pages appearing out of sequence
- First page showing middle/end of track instead of beginning
- Poor centering of track segments on pages

### Solution
Changed from `set()` to ordered `list()` with separate `seen_tiles` set in `utils.py`:

```python
# Before (WRONG):
list_index_found = set()
list_index_found.add((col, row))

# After (CORRECT):
list_index_found = []
seen_tiles = set()
if (col, row) not in seen_tiles:
    list_index_found.append((col, row))
    seen_tiles.add((col, row))
```

### Why It Works
1. **Preserves GPS chronology**: Tiles added in exact GPS track order
2. **Maintains uniqueness**: `seen_tiles` set prevents duplicates
3. **Enables proper grouping**: `put_tiles_in_pages()` starts from chronologically first tile
4. **Keeps centering**: Growing bounding box algorithm still centers track on each page

## Design Decisions

### Overlap is Intentional
Pages intentionally overlap (average 19%) to allow:
- Physical alignment when printing multiple pages
- Continuity verification between consecutive pages
- Easier navigation across page boundaries

### Growing Bounding Box
The `min_col`/`min_row` updates in `put_tiles_in_pages()` are intentional:
- Centers the GPS track on each page
- Creates natural page boundaries
- Optimizes tile usage per page

## Running Individual Tests

### Test Chronological Ordering
```bash
docker run --rm gpx-test python3 -m pytest tests/test_processing_steps.py::TestProcessingSteps::test_step1_grouping_medium_dataset -v -s
```

### Test Overlap Analysis
```bash
docker run --rm gpx-test python3 -m pytest tests/test_processing_steps.py::TestProcessingSteps::test_step4_full_pipeline_medium -v -s
```

### Simple Chronology Check
```bash
docker run --rm gpx-test python3 simple_test.py
```

## Test Coverage

- ✅ Chronological ordering
- ✅ Page grouping algorithm
- ✅ Corner tile calculation
- ✅ Page grid filling
- ✅ Overlap analysis
- ✅ Duplicate detection
- ✅ Full pipeline integration
- ✅ Multiple dataset sizes
- ✅ Real GPX data (not synthetic)

## Continuous Testing

Add to CI/CD:
```yaml
- name: Run GPX Processing Tests
  run: |
    docker build -f Dockerfile.test -t gpx-test .
    docker run --rm gpx-test
```

## Adding New Test Cases

1. Add GPX file to `gpx_files/`
2. Update `extract_test_data.py` to include new dataset
3. Run `python3 extract_test_data.py`
4. Tests automatically use new fixtures
5. Report includes new dataset analysis
