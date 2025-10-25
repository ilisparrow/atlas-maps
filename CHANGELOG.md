# Changelog

## Recent Changes

### Page Generation Fix
- Fixed chronological ordering of pages to follow GPS track sequence
- Changed from `set()` to ordered `list()` in tile collection to preserve GPS order
- Pages now correctly start from beginning of track

### Navigation Markers
- Added directional markers on each page showing next/previous page location
- Markers include arrow indicating direction and page number
- Positioned at page edges for easy reference when using printed maps

### Testing Infrastructure
- Added comprehensive unit tests for page generation algorithm
- Tests verify chronological ordering, tile grouping, and coverage
- GitHub Actions workflow for automated testing
- Full pipeline test with profiling and PDF generation

### Performance
- Tile extraction: ~230,000 points/sec
- Page grouping: 1-2 seconds for typical routes
- PDF generation: ~1.5s per page (bottleneck: tile fetching)

### Documentation
- Updated README with clearer feature descriptions
- Added testing instructions
- Created detailed technical documentation
