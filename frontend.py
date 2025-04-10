import os
import streamlit as st
import streamlit_analytics2 as streamlit_analytics
import requests
from io import BytesIO

from dotenv import load_dotenv
# Set page configuration
st.set_page_config(layout="wide", page_title="Atlas Generator", page_icon="./icon.ico")
load_dotenv()
SERVERLESS_ADDRESS = os.getenv('SERVERLESS_ADDRESS')
# Page title
st.title("Atlas creator from GPX")
streamlit_analytics.start_tracking(load_from_json="analytics.json")
streamlit_analytics.track()

# File uploader for a single GPX file
uploaded_file = st.file_uploader("Choose a GPX file", accept_multiple_files=False, type=["gpx"])

# Create a sidebar for configuration options
st.sidebar.header("Map Configuration")

# Add a selector for tile source
tile_source = st.sidebar.selectbox(
    "Select map tile source",
    options=["IGN", "OSM", "TOPO"],
    index=0,  # Default to IGN
    help="IGN: French National Geographic Institute (works best in France)\nOSM: OpenStreetMap (worldwide)\nTOPO: OpenTopoMap (worldwide with topographic lines)"
)

# Add a color picker for the track line
line_color = st.sidebar.color_picker(
    "Track line color",
    value="#B700FF",  # Default purple color
    help="Choose the color for the GPX track line"
)

# Add a note about IGN maps
if tile_source == "IGN":
    st.sidebar.info("IGN maps are optimized for France. For other regions, consider using OSM or TOPO.")

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
        
        # Add the parameters to the request
        params = {
            '_tile_source': tile_source,
            '_line_color': line_color
        }

        # Sending the POST request
        response = requests.post(url, files=files, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            with open('output.pdf', 'wb') as f:
                f.write(response.content)

            with open('output.pdf', 'rb') as f:
                pdf_data = f.read()

            # Allow the user to download the PDF
            st.success("Atlas generated successfully!")
            st.download_button(label="Download PDF", data=response.content, file_name="atlas.pdf", mime="application/pdf")

        else:
            st.error(f"Failed to generate the PDF. Status code: {response.status_code}")
            st.error("Please try again or try with a different tile source.")
streamlit_analytics.stop_tracking(save_to_json="analytics.json",unsafe_password=os.getenv("ANALYTICS_PASS"))
# Footer captions
st.caption("For suggestions, or bugs please feel free to reach out at: contact(at)iliasamri.com")
st.caption("All of this is possible thanks to multiple open source projects, data from IGN, OpenStreetMap, OpenTopoMap, icon from maxicons/flaticon.")
