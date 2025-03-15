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
image = modal.Image.debian_slim().pip_install("streamlit", "numpy", "pandas", "gpxpy", "python-dotenv", "Pillow",
                                              "asyncio", "aiohttp", "stqdm", "pyproj","fastapi")

app = modal.App(
    name="serve-atlas", image=image
)

streamlit_script_local_path = Path(__file__).parent / "utils.py"
streamlit_script_remote_path = Path("/root/utils.py")

if not streamlit_script_local_path.exists():
    raise RuntimeError(
        "app.py not found! Place the script with your streamlit app in the same directory."
    )

streamlit_script_mount = modal.Mount.from_local_file(
    streamlit_script_local_path,
    streamlit_script_remote_path,
)
streamlit_utils_mount = modal.Mount.from_local_file("page_generation.py", "/root/page_geneneration.py" )
streamlit_env_mount = modal.Mount.from_local_file(".env", "/root/.env" )
streamlit_icon_mount = modal.Mount.from_local_file("icon.ico", "/root/icon.ico" )
streamlit_font_mount = modal.Mount.from_local_file("fonts/FreeMono.ttf", "/usr/share/fonts/truetype/freefont/FreeMono.ttf" )
streamlit_font_bold_mount = modal.Mount.from_local_file("fonts/FreeMonoBold.ttf", "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf" )


@app.function(
    timeout=600,
    allow_concurrent_inputs=100,
    image=image,
    mounts=[streamlit_script_mount,streamlit_utils_mount,streamlit_env_mount,streamlit_icon_mount,streamlit_font_mount,streamlit_font_bold_mount],)
@web_endpoint(method="POST")
async def run(gpx_file: UploadFile = File(...)):
    contents = await gpx_file.read()
    gpx = gpxpy.parse(contents.decode('utf-8'))
    file_path = await main(gpx)

    return FileResponse(
        file_path,
        media_type="application/pdf", filename="map.pdf"
    )
