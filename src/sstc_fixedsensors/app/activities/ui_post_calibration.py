import streamlit as st
from sstc_utils.utils import fetch_markdown_instructions_from_github



def load_instructions():
    instructions_md = fetch_markdown_instructions_from_github(url='instructions.md')
    st.markdown(instructions_md)