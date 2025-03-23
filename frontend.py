import os

import streamlit as st
import requests
from io import BytesIO

from dotenv import load_dotenv

# Set page configuration
st.set_page_config(layout="wide", page_title="Atlas Generator", page_icon="./icon.ico")
load_dotenv()
SERVERLESS_ADDRESS = os.getenv('SERVERLESS_ADDRESS')
# Page title
st.title("Atlas creator from GPX")

# File uploader for a single GPX file
uploaded_file = st.file_uploader("Choose a GPX file", accept_multiple_files=False, type=["gpx"])

# Add a selector for tile source
tile_source = st.selectbox(
    "Select map tile source",
    options=["IGN", "OSM"],
    index=0  # Default to IGN
)

# Button to trigger the generation
button_pressed = st.button("Generate !")

if uploaded_file and button_pressed:
    # Read the content of the uploaded file
    file_content = uploaded_file.getvalue()
    file_name = uploaded_file.name

    with st.spinner("Uploading and processing (It might take up to 5 minutes) ..."):
        # URL to which the request is sent
        url = SERVERLESS_ADDRESS

        # Prepare the file in the correct format for the API
        files = {'gpx_file': (file_name, file_content, 'application/gpx+xml')}
        
        # Add the tile_source parameter to the request
        params = {'_tile_source': tile_source}

        # Sending the POST request
        response = requests.post(url, files=files, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            with open('output.pdf', 'wb') as f:
                f.write(response.content)

            with open('output.pdf', 'rb') as f:
                pdf_data = f.read()

            # Allow the user to download the PDF
            st.download_button(label="Download PDF", data=response.content, file_name="atlas.pdf", mime="application/pdf")

        else:
            st.error("Failed to generate the PDF. Please try again.")

# Footer captions
st.caption("For suggestions, or bugs please feel free to reach out at: contact(at)iliasamri.com")
st.caption("All of this is possible thanks to multiple open source projects, data from IGN, icon from maxicons/flaticon.")
