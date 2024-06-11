import os
from pathlib import Path
import streamlit as st
from streamlit_activities_menu import build_activities_menu, get_available_activities


st.set_page_config(
    layout='wide',
    page_title='SSTC',
    page_icon='https://github.com/SITES-spectral/sstc-assets/blob/main/src/sstc_assets/favicons/SITES_favicon.png?raw=true',
    initial_sidebar_state='expanded',
    )


def initialize():
    APP_DIRPATH = Path(__file__).resolve().parents[0]
    if 'METADATA' not in st.session_state:
        st.session_state['METADATA'] = {}
    if 'APP' not in st.session_state:
        st.session_state['APP'] = {}
    if 'APP_DIRPATH' not in st.session_state['APP']:
        st.session_state['APP']['APP_DIRPATH'] = {}
    
       
    #
    st.session_state['APP']['APP_DIRPATH'] = APP_DIRPATH
    st.session_state['APP']['ACTIVITIES_FILEPATH'] = os.path.join(
        APP_DIRPATH, 
        "app_activities.yaml")
    st.session_state['APP']['ACTIVITIES_DIRPATH'] =  os.path.join(
        APP_DIRPATH, 
        "activities/" )
    #
    st.session_state['APP']['MARKDOWN_DIRPATH'] = os.path.join(
        APP_DIRPATH,
        'markdown/')
    st.session_state['APP']['INSTRUCIONS_FILEPATH'] = os.path.join(
        st.session_state['APP']['MARKDOWN_DIRPATH'],
        'instructions.md' )
    #
    st.session_state['APP']['SSTC_LOGO_FILEPATH'] = "https://github.com/SITES-spectral/sstc-assets/blob/main/src/sstc_assets/logos/SITES_spectral_LOGO.png?raw=true"

def run():
    initialize()
    
    LOGO_SIDEBAR_URL = st.session_state['APP']['SSTC_LOGO_FILEPATH']

    if LOGO_SIDEBAR_URL: st.sidebar.image(
            LOGO_SIDEBAR_URL,             
            caption= 'Swedish Infrastructure for Ecosystem Science (SITES) Spectral'
            )
        
    # Load the available services
    ACTIVITIES_FILEPATH = st.session_state['APP']['ACTIVITIES_FILEPATH']
    ACTIVITIES_DIRPATH =  st.session_state['APP']['ACTIVITIES_DIRPATH']

    # Load the yaml with core services as activities    
    core_activities =  get_available_activities(
        activities_filepath=ACTIVITIES_FILEPATH        
    )
       
    build_activities_menu(
            activities_dict=core_activities, 
            label='**Activities:**', 
            key='activitiesMenu', 
            activities_dirpath=ACTIVITIES_DIRPATH,
            disabled=False
            )

    st.sidebar.divider()
    
if __name__ == '__main__':
    run()
else:
    st.error('The app failed initialization. Report issue to mantainers in github')