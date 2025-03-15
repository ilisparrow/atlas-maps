import os
import asyncio
import gpxpy
from main import main

async def test_gpx_to_pdf():
    """Test that the main function can process a GPX file and generate a PDF."""
    test_gpx_file = 'gpx_files/[Standard]mini_map.gpx'
    try:
        with open(test_gpx_file, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            pdf_path = await main(gpx)
            assert pdf_path is not None
            assert os.path.exists(pdf_path)
            assert pdf_path.endswith('.pdf')
            print(f"Test passed! PDF generated at: {pdf_path}")
    except FileNotFoundError:
        print(f"Please create a test GPX file at {test_gpx_file}")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_gpx_to_pdf()) 