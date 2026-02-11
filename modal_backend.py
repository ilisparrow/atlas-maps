import shlex
import subprocess
from pathlib import Path

import asyncio

import gpxpy

from utils import main
import modal
from modal import App, web_endpoint
from fastapi import Response
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, UploadFile

streamlit_script_local_path = Path(__file__).parent / "utils.py"

if not streamlit_script_local_path.exists():
    raise RuntimeError(
        "app.py not found! Place the script with your streamlit app in the same directory."
    )

image = (
    modal.Image.debian_slim()
    .pip_install("streamlit", "numpy", "pandas", "gpxpy", "python-dotenv", "Pillow",
                 "asyncio", "aiohttp", "stqdm", "pyproj", "fastapi")
    .add_local_file(str(streamlit_script_local_path), "/root/utils.py")
    .add_local_file("page_generation.py", "/root/page_generation.py")
    .add_local_file(".env", "/root/.env")
    .add_local_file("icon.ico", "/root/icon.ico")
    .add_local_file("fonts/FreeMono.ttf", "/usr/share/fonts/truetype/freefont/FreeMono.ttf")
    .add_local_file("fonts/FreeMonoBold.ttf", "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf")
)

app = modal.App(
    name="serve-atlas", image=image
)


@app.function(
    timeout=600,
    allow_concurrent_inputs=100,
)
@web_endpoint(method="POST")
async def run(gpx_file: UploadFile = File(...), _tile_source:str = "IGN", _line_color:str = "#B700FF"):
    contents = await gpx_file.read()
    gpx = gpxpy.parse(contents.decode('utf-8'))
    file_path = await main(gpx, tile_source=_tile_source, line_color=_line_color)

    return FileResponse(
        file_path,
        media_type="application/pdf", filename="map.pdf"
    )
