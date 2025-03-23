import base64
import io
import math
from pyproj import Transformer
import requests
import gpxpy
import gpxpy.gpx
import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import copy
from dotenv import load_dotenv
import asyncio
import aiohttp
from stqdm import stqdm
from collections import defaultdict
import numpy as np
import pandas as pd
from page_generation import get_filled_pages

# DONE : We need 14 images per A4 paper sheet
# DONE : Fixe weird bug, always saving the same image for TRACE
# DONE : Fixe weird Offset
# DONE : Put key in env
# DONE : Add number to the pages and scale
# DONE : Exprot PDF
# DONE : Profile and optimize : Make it faster by reunning it async
# DONE : DO UI
# DONE : Add sttqdm
# DONE : Make the color and line thickness variable
# DONE : When adding a new page, check if the top, left block is not already in the last page, to not have much overlap
# TODO : Give choice Portrait, Landscape
# TODO : Make number of tiles variables
# TODO : Give choice A4, A3
# TODO : Deploy a small pocketbase or sqlite with files to save the GPX
# TODO : Add Optional Grid
# TODO : Clean and refactor
# TODO : Maybe fetch all images of all pages at once.
# DONE : Give choice OSM or IGN
# TODO : Give choice add legend page

load_dotenv()
NUMBER_ROWS = 14  # 14
NUMBER_COLUMNS = 9  # 9
IGN_KEY = os.getenv("IGN_KEY")
resolution = 2.3886  # meters per px
Distance_in_scale_in_m = 500
half_k_in_px = Distance_in_scale_in_m / resolution
LINE_WIDTH = 8
LINE_COLOR = "#B700FF"
TILE_SOURCE = "IGN"  # Default to IGN, can be changed to "OSM"

def lat_long_to_osm_tile(lat, lon, zoom=16):
    """Convert latitude/longitude to OSM tile coordinates"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    # Calculate offset within the tile (0-256 px)
    x_offset = ((lon + 180.0) / 360.0 * n - xtile) * 256
    y_offset = ((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n - ytile) * 256
    return xtile, ytile, x_offset, y_offset

def vectorized_lat_long_to_osm_tile(lats, longs, zoom=16):
    """Vectorized version to convert multiple points to OSM tile coordinates"""
    lats_rad = np.radians(lats)
    n = 2.0 ** zoom
    
    xtiles = ((longs + 180.0) / 360.0 * n).astype(int)
    ytiles = ((1.0 - np.log(np.tan(lats_rad) + (1 / np.cos(lats_rad))) / np.pi) / 2.0 * n).astype(int)
    
    # Calculate offsets within tiles (0-256 px)
    x_offsets = ((longs + 180.0) / 360.0 * n - xtiles) * 256
    y_offsets = ((1.0 - np.log(np.tan(lats_rad) + (1 / np.cos(lats_rad))) / np.pi) / 2.0 * n - ytiles) * 256
    
    return xtiles, ytiles, x_offsets, y_offsets

async def get_image_with_request_from_col_row_fast(col_row, tile_source=TILE_SOURCE):
    async with aiohttp.ClientSession() as session:
        if tile_source.upper() == "IGN":
            # IGN tile URL
            url = f"https://data.geopf.fr/private/wmts?apikey=ign_scan_ws&SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX=16&TILEROW={col_row[1]}&TILECOL={col_row[0]}&FORMAT=image%2Fjpeg"
            
            async with session.get(url) as response:
                if response.status != 200:
                    # If IGN request fails, create a blank tile
                    image = Image.new("RGB", (256, 256), (240, 240, 240))
                    draw = ImageDraw.Draw(image)
                    draw.text((10, 120), f"Tile: {col_row[0]},{col_row[1]}", fill=(0, 0, 0))
                    draw.rectangle((0, 0, 255, 255), outline=(0, 0, 0), width=1)
                    return col_row, image
                
                image_data = await response.read()
        
        elif tile_source.upper() == "OSM":
            # OSM tile URL
            zoom_level = 16  # Same zoom level as IGN
            url = f"https://a.tile.openstreetmap.org/{zoom_level}/{col_row[0]}/{col_row[1]}.png"
            
            # Create proper headers for OSM - they require a User-Agent
            headers = {
                "User-Agent": "GPX Map Generator/1.0",
                "Accept": "image/png,image/*;q=0.9"
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    # If the request fails, create a blank image with the tile coordinates
                    image = Image.new("RGB", (256, 256), (240, 240, 240))
                    draw = ImageDraw.Draw(image)
                    draw.text((10, 120), f"Tile: {col_row[0]},{col_row[1]}", fill=(0, 0, 0))
                    draw.rectangle((0, 0, 255, 255), outline=(0, 0, 0), width=1)
                    return col_row, image
                
                image_data = await response.read()

    try:
        # Process the image data if necessary and return the image
        image = Image.open(io.BytesIO(image_data))
        return col_row, image
    except Exception as e:
        # Fallback if image can't be opened
        print(f"Error opening tile at {col_row}: {e}")
        image = Image.new("RGB", (256, 256), (240, 240, 240))
        draw = ImageDraw.Draw(image)
        draw.text((10, 120), f"Error: {col_row[0]},{col_row[1]}", fill=(255, 0, 0))
        draw.rectangle((0, 0, 255, 255), outline=(255, 0, 0), width=1)
        return col_row, image


def get_tile_number_from_coord(lat, long, tile_source=TILE_SOURCE):
    if tile_source.upper() == "OSM":
        # Use OSM tile numbering
        return lat_long_to_osm_tile(lat, long)
    else:
        # Original IGN code
        TRAN_4326_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857")
        # ORiginal coordinates for our resolution
        # resolution = 0.5971642835#meters per px
        tile_size_in_meters = 256 * resolution
        x0, y0 = -20037508, 20037508
        x, y = TRAN_4326_TO_3857.transform(lat, long)
        delta_x, delta_y = x - x0 - (resolution * 205), y0 - y - (
            resolution * 146
        )  # TODO: FIXE For some reason their is an offset, maybe it has to do with the way the tiles are fetched
        col, row = delta_x // tile_size_in_meters, delta_y // tile_size_in_meters
        offset_x, offset_y = ((delta_x % tile_size_in_meters) / resolution), (
            delta_y % tile_size_in_meters / resolution
        )
        return col, row, offset_x, offset_y


def vectorized_get_tile_number_from_coord(lats, longs, tile_source=TILE_SOURCE):
    if tile_source.upper() == "OSM":
        # Use OSM tile calculation
        return vectorized_lat_long_to_osm_tile(lats, longs)
    else:
        # Original IGN code
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        xs, ys = transformer.transform(longs, lats)
        tile_size_in_meters = 256 * resolution
        x0, y0 = -20037508, 20037508
        delta_xs = xs - x0 - (resolution * 205)
        delta_ys = y0 - ys - (resolution * 146)
        cols = np.floor(delta_xs / tile_size_in_meters)
        rows = np.floor(delta_ys / tile_size_in_meters)
        offset_xs = (delta_xs % tile_size_in_meters) / resolution
        offset_ys = (delta_ys % tile_size_in_meters) / resolution
        return cols, rows, offset_xs, offset_ys


def annotate_image(image, number, position, rectangle_position):
    """
    Annotates a PIL image with a number at a specific position
    and draws a rectangle at the specified position.

    Args:
        image (PIL.Image.Image): The input image.
        number (int): The number to be written on the image.
        position (tuple): The top-left position (x, y) where the number should be written.
        rectangle_position (tuple): The position (left, top, right, bottom) of the rectangle.

    Returns:
        PIL.Image.Image: The annotated image.
    """
    # Create a copy of the input image
    annotated_image = image.copy()

    # Create a drawing object
    draw = ImageDraw.Draw(annotated_image)

    # Define the font style and size
    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 60)
    font_bold = ImageFont.truetype(
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 60
    )

    # Write the number at the specified position
    draw.text(position, "N° : " + str(number), font=font_bold, fill=(255, 255, 255))
    draw.text(position, "N° : " + str(number), font=font, fill=(0, 0, 0))

    # Write the scale at the write pos
    draw.text(
        (rectangle_position[0], rectangle_position[1]),
        str(Distance_in_scale_in_m) + " m",
        font=font_bold,
        fill=(255, 255, 255),
    )
    draw.text(
        (rectangle_position[0], rectangle_position[1]),
        str(Distance_in_scale_in_m) + " m",
        font=font,
        fill=(0, 0, 0),
    )

    # Draw a rectangle
    draw.rectangle(rectangle_position, fill=(0, 0, 0), outline=(255, 255, 255))

    return annotated_image


def calculate_gpx_points(col_idx, row_idx, row, col, gpx_points):

    pos = []
    if (row, col) in gpx_points:
        for gpx_point in gpx_points[row, col]:
            center_x, center_y = gpx_point
            center_x = center_x + 256 * col_idx
            center_y = center_y + 256 * row_idx
            pos.append((center_x, center_y))
    return pos


def draw_gpx_points(original_image, row, col, gpx_points):

    # Create a drawing object
    # col = col-1  #SOme reason it's shifted
    row = row  # SOme reason it's shifted
    col = col  # SOme reason it's shifted

    if (row, col) in gpx_points:
        for gpx_point in gpx_points[row, col]:
            center_x, center_y = gpx_point

            draw = ImageDraw.Draw(original_image)
            radius = 10
            # Define the circle boundary coordinates
            x0 = center_x - radius
            y0 = center_y - radius
            x1 = center_x + radius
            y1 = center_y + radius
            # Draw a red circle on the image
            draw.rectangle(
                (0, 0, original_image.width, original_image.height),
                outline=(0, 0, 0),
                width=3,
            )
            draw.ellipse([(x0, y0), (x1, y1)], fill="red", outline="black")
    else:
        draw = ImageDraw.Draw(original_image)
        draw.rectangle(
            (0, 0, original_image.width, original_image.height),
            outline=(0, 0, 0),
            width=3,
        )

    return original_image


def get_concat_h_blank(im1, im2, color=(0, 0, 0)):
    dst = Image.new("RGB", (im1.width + im2.width, max(im1.height, im2.height)), color)
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


def get_concat_h_blank_gpt(*images):
    widths, heights = zip(*(im.size for im in images))
    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new("RGB", (total_width, max_height), color=(255, 255, 255))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    return new_im


def get_concat_v_blank_gpt(*images):
    widths, heights = zip(*(im.size for im in images))
    total_height = sum(heights)
    max_width = max(widths)

    new_im = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))

    y_offset = 0
    for im in images:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]

    return new_im


def get_concat_v_blank(im1, im2, color=(0, 0, 0)):
    dst = Image.new("RGB", (max(im1.width, im2.width), im1.height + im2.height), color)
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def append_or_create_point(
    gpx_points, col, row, gpx_point_in_px_x, gpx_point_in_px_y, lat
):
    """Appends the point to the gpx_points dictionary if it exists, or creates the gpx_points dictionary with the point as the only element.

    Args:
      gpx_points: The gpx_points dictionary.
      col: The column of the point.
      row: The row of the point.
      gpx_point_in_px_x: The x-coordinate of the point in pixels.
      gpx_point_in_px_y: The y-coordinate of the point in pixels.

    Returns:
      The gpx_points dictionary.
    """
    if (col, row) in gpx_points:
        gpx_points[(col, row)].append((gpx_point_in_px_x, gpx_point_in_px_y))
    else:
        gpx_points[(col, row)] = [(gpx_point_in_px_x, gpx_point_in_px_y)]
    return gpx_points


def draw_line(list_of_circles, original_image):
    image = Image.new("RGB", original_image.size, "black")
    mask = Image.new("L", original_image.size, "black")

    draw = ImageDraw.Draw(image)
    draw_mask = ImageDraw.Draw(mask)
    radius = 5
    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 24)
    i = 0
    list_of_circles = [x for x in list_of_circles if x is not None]
    for idx, (x, y) in enumerate(list_of_circles):
        # draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="white", fill='red')
        if idx < len(list_of_circles) - 1:
            i += 1
            # For debug
            # draw.text((list_of_circles[idx][0], list_of_circles[idx][1]), str(f'idx : {i}, ({int(list_of_circles[idx][0])},{int(list_of_circles[idx][1])})'), font=font, fill="white")
            draw.line(
                (
                    list_of_circles[idx][0],
                    list_of_circles[idx][1],
                    list_of_circles[idx + 1][0],
                    list_of_circles[idx + 1][1],
                ),
                fill=LINE_COLOR,
                width=LINE_WIDTH,
            )
            draw_mask.line(
                (
                    list_of_circles[idx][0],
                    list_of_circles[idx][1],
                    list_of_circles[idx + 1][0],
                    list_of_circles[idx + 1][1],
                ),
                fill="white",
                width=LINE_WIDTH,
            )
    return image, mask


def get_pos_gpx_in_px_in_page(page, point):

    flatten_page = [element for sublist in page for element in sublist]

    try:
        index = flatten_page.index(point)
        # Calculate the 2D index from the 1D index
        i = index // len(page[0])
        j = index % len(page[0])
        return (i * 256, j * 256)
    except ValueError:
        pass


pages = []
image_pages_for_export = []

def displayPDF(file):
    # Opening file from file path
    file_size = os.path.getsize(file)  # Get file size in bytes
    MAX_FILE_SIZE_IN_MB = 50
    max_file_size = MAX_FILE_SIZE_IN_MB * 1024 * 1024  # 10 MB in bytes
    megabytes = max_file_size / (1024**2)
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        return base64_pdf

async def main(gpx, tile_source=TILE_SOURCE):
    # Get all the track points from the GPX file
    track_points = gpx.get_points_data()

    tiles = []
    gpx_in_px = []
    gpx_points = {}
    page = [[(0, 0)] * NUMBER_ROWS for _ in range(NUMBER_COLUMNS)]

    list_index_found = set()
    gpx_points = defaultdict(list)

    for track in gpx.tracks:
        for segment in track.segments:
            # Assume each segment.points is a list of objects with .latitude and .longitude attributes
            data = pd.DataFrame([(p.latitude, p.longitude) for p in segment.points], columns=['lat', 'long'])

            # Vectorized coordinate transformation - pass tile_source
            cols, rows, offset_xs, offset_ys = vectorized_get_tile_number_from_coord(
                data['lat'].values, data['long'].values, tile_source
            )

            # Processing results
            for i, (col, row, ox, oy) in enumerate(zip(cols, rows, offset_xs, offset_ys)):
                point = segment.points[i]
                gpx_points[(col, row)].append((ox, oy, point.latitude))
                list_index_found.add((col, row))

    # Convert set back to list if needed
    list_index_found = list(list_index_found)

    pages = get_filled_pages(list_index_found, NUMBER_COLUMNS, NUMBER_ROWS)

    global_image = None
    image_pages_for_export = []

    page_number = 0
    for _page in tqdm(pages):
        list_post = []
        for key in gpx_points.keys():
            tile_pos = get_pos_gpx_in_px_in_page(_page, key)
            if not tile_pos == None:
                for point in gpx_points[key]:
                    list_post.append(
                        copy.deepcopy((tile_pos[0] + point[0], tile_pos[1] + point[1]))
                    )

        ###############
        #'''
        flattened_list = [item for sublist in _page for item in sublist]
        tasks = []
        for col_row in flattened_list:
            task = asyncio.create_task(
                get_image_with_request_from_col_row_fast(col_row, tile_source)
            )
            tasks.append(task)

        images = await asyncio.gather(*tasks)
        image_dict = {col_row: image for col_row, image in images}
        sorted_images = sorted(images, key=lambda x: flattened_list.index(x[0]))
        sorted_images = [image for _, image in sorted_images]
        grid = [
            sorted_images[i : i + NUMBER_ROWS]
            for i in range(0, len(sorted_images), NUMBER_ROWS)
        ]
        stitched_horizontal = [get_concat_v_blank_gpt(*row) for row in grid]
        global_image = get_concat_h_blank_gpt(*stitched_horizontal)

        gpx_trace_img, mask = draw_line(list_post, global_image)

        today = str(datetime.date.today()).replace("-", "")
        folderpath = "./output/" + today
        try:
            os.makedirs(folderpath)
        except OSError:
            pass

        # Create a mask of the white pixels in the first image
        mask = mask.point(
            lambda p: p > 128 and 255
        )  # Threshold the image to white (pixel value > 128)

        # Paste the first image's white pixels onto the second image
        global_image.paste(gpx_trace_img, (0, 0), mask=mask)
        # Add scale and page number to page
        global_image = annotate_image(
            global_image, page_number, (20, 20), (20, 75, 20 + half_k_in_px, 80)
        )
        
        image_pages_for_export.append(copy.deepcopy(global_image))
        page_number += 1

    file_name = "OUTPUT.pdf"
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
    output_dir_pdf_path = "./output/PDFs/"
    os.makedirs(output_dir_pdf_path, exist_ok=True)
    file_name = output_dir_pdf_path + timestamp + ".pdf"
    if len(image_pages_for_export) == 0:
        file_name = None
    elif len(image_pages_for_export) == 1:
        image_pages_for_export[0].save(
            file_name, "PDF", resolution=100.0, save_all=True
        )
    else:
        image_pages_for_export[0].save(
            file_name,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=image_pages_for_export[1:],
        )

    return file_name