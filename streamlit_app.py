import streamlit as st
# Set the path to your scripts
st.set_page_config(
    page_title="Rule Creator App",
    layout="wide",  # You can use "centered" for a more constrained default
)
import os
import sys
from pathlib import Path
import streamlit_score_card
import rule_editor
# from pyngrok import ngrok, conf
# import logging


# ngrok.set_auth_token("2q1SaIUluog1Ax1nrExFuOjcGad_3muxBvLCxeb5DDdZJs88")
# public_url = ngrok.connect(port=8508)
# print(f" * ngrok tunnel URL: {public_url}")

# Inject custom CSS for a custom width
# st.markdown(
#     """
#     <style>
#     .block-container {
#         max-width: 1000px;  /* Set the desired maximum width */
#         margin: 0 auto;     /* Center the content */
#         padding: 30px;      /* Optional: add padding for better appearance */
#         background-color:grey;
#         # color:red;

#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )
# sys.path.insert(1, "/home/ubuntu/Meeting_Streamlit")

# Import the main function from the script
st.title("Scoring App")

@st.cache_resource
def load_script(script_path):
    """Load the script content and return it as a string."""
    with open(script_path, "r") as file:
        return file.read()

# logging.basicConfig(level=logging.INFO)

# Load scripts with caching
script1_code = load_script("Scoring_streamlit.py")
script2_code = load_script("streamlit_score_card.py")
script3_code = load_script("Rule_creation.py")
script4_code = load_script("rule_editor.py")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Score_weights", "Score_card", "Rule_creation","Rule_editor"])

# Execute script code in respective tabs
with tab1:
    exec(script1_code)

with tab2:
    streamlit_score_card.main()

with tab3:
    exec(script3_code)

with tab4:
    rule_editor.edit_rule_interface()
    # exec(script4_code)
