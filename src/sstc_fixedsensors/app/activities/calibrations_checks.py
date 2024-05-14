import streamlit as st
import pandas as pd
from calval import calibration
from schemas import SITES
import os
import requests

# Decagon
# Skye sensors
"""
    General naming convention: Up_Wavelength, Dw_Wavelength
    
    For example (Decagon Sensors):
    ------------------------------
        
    Up_630, Dw_630  ==> Red Channel
    Up_800, Dw_800  ==> NIR Channel
    
    If there are multiple sensor pairs, the column name must be:
    
    Up_630_1, Dw_630_1  ==> Red Channel
    Up_800_1, Dw_800_1  ==> NIR Channel 
"""
def fetch_markdown_instructions_from_github():
    
    url = "https://raw.githubusercontent.com/SITES-spectral/sstc-fixedsensors/main/src/sstc_fixedsensors/app/instructions.md"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None


@st.cache_data()
def load_instructions():
    instructions_md = fetch_markdown_instructions_from_github()
    st.markdown(instructions_md)
    

def initialize()-> dict:
    if 'research_stations' not in st.session_state and SITES is not None:
        st.session_state['research_stations'] = SITES.get(
            'research_stations', {
                'SITES Spectral': {
                    'acronym': 'SSTC', 
                    'name': 'SITES Spectral Thematic Center'}})

def station_selectbox()->str:
    research_stations =  st.session_state['research_stations']
    station = st.selectbox(
        'Choose your Station:',
        options=research_stations.keys()
        )
    st.session_state['station'] = station
    return station

def sstc_read_csv(uploaded_file, header= 1,  delete_rows=[]): 

    
    _to_delete = []

    for i in data.index:
        if int(i) in delete_rows:
            _to_delete.append(i)
    
    data.drop(_to_delete, inplace=True)

    return data

@st.experimental_dialog('Instructions')
def show_instructions_dialog():
    load_instructions()

"""
@st.cache_data(experimental_allow_widgets=True)
def load_calibration_file_as_dataframe(
    delimiter=',',
    decimal='.',
    header=1,
    encoding='utf-8'
    ):
"""
    

@st.experimental_dialog('calibration dataset')
def show_raw_calibration(raw_calibration_df:pd.DataFrame):
    if raw_calibration_df is not None:
        st.write(raw_calibration_df)

def run():
    initialize()

    _, instructions_col1, header_stations_col = st.columns([3,1,1], gap='small')
    station = None
    with instructions_col1:
        with st.container(border=True):
            if st.button('Instructions'):
                show_instructions_dialog()
                
        with header_stations_col:
            station = station_selectbox()

    with st.expander('**Step 01**: Load calibration dataset', expanded=True):
        step01_col1, step01_col2 = st.columns([2,1])

        with step01_col1:
            uploaded_file = st.file_uploader(
                label="Choose a calibration file:",
                type=["dat", "csv", "txt", "tsv"])
            
            if uploaded_file is not None:
                calibration_df = pd.read_csv(
                    uploaded_file, 
                    delimiter=',',
                    decimal='.',
                    header=1,
                    encoding='utf-8',        
                    )
                
            else:
                calibration_df = None

    if 'calibration_df' not in st.session_state:
        st.session_state['calibration_df'] = None

    if calibration_df is not None:
        st.session_state['calibration_df'] = calibration_df
    

    if st.session_state['calibration_df'] is not None:
            
        with st.expander('**STEP 02**: dataprep'):
            cal_df = st.session_state['calibration_df']
            columns = list(cal_df.columns)
            timestamp_col = None
            if 'delete_rows' not in st.session_state:
                st.session_state['delete_rows'] = []

            message = st.empty()
            

            # ---

            step02_col1, step02_col2 = st.columns([1,2], gap='small')

            with step02_col1:
                delete_rows = st.multiselect(
                    label='**delete** row number:',
                    options=[0,1],
                    )
                st.session_state['delete_rows']= delete_rows

            with step02_col2:
                cal_df = cal_df.drop(st.session_state['delete_rows'], axis=0)
                if 'TIMESTAMP' in columns:
                    try:                        
                        timestamp_col = 'TIMESTAMP'
                        cal_df[timestamp_col] = pd.to_datetime(
                            cal_df['TIMESTAMP'],
                            format='%Y-%m-%d %H:%M:%S'
                            )                
                        
                        none_indices = [int(i) for i in  cal_df.loc[cal_df[timestamp_col].isna()].index]
                        
                        if len(none_indices) >0:
                            message.warning(f'Please remove the rows where `TIMESTAMP` is empty: rows {none_indices}')
                        else:
                            message.success('`TIMESTAMP` recognized. Continue to **STEP 03**')
                            st.balloons()

                    except:
                        message.error('`TIMESTAMP` cannot be processed. Delete extra rows affecting data values.')
                else:
                    message.warning('`TIMESTAMP` column not found')
            
                st.session_state['cal_df'] = cal_df
                st.dataframe(cal_df)
        with st.expander('**STEP 03**: Revise channels pairs and center wavelengths for each channel'):
            do_not_include_columns = [
                'TIMESTAMP', 
                'RECORD',
                'BattV_Min',
                'PTemp_C_Avg',
                'Temp_Avg',
                'Temp',
                'PTemp',
                ]
            
            
        
            all_channels = [c for c in columns if c not in do_not_include_columns]

            # split the column names and select the first item in the list which is expected to be `Up` or `Dw`.
            up_channels = pd.DataFrame.from_dict({
                'Up': [u for u in all_channels if u.split(sep='_')[0] in ['Up', 'up'] ]})
          
            down_channels = pd.DataFrame.from_dict({'Down': [d for d in all_channels if  d.split(sep='_')[0] in ['Dw', 'dw'] ]})
           
            matched_channels = pd.concat([up_channels, down_channels], axis=1)
            matched_channels['sensor_sites_named'] = None
            matched_channels['sensor_model'] = None
            
            matched_channels['center_wavelength_nm'] = None
            matched_channels['mast_height_m'] = None
            matched_channels['is_validated'] = False
            if matched_channels is not None:
                sensor_brands = {'Skye': {'center_wavelengths_nm': [469, 530, 531, 532, 552, 570, 640, 644, 645, 650, 704, 740, 810, 856, 858, 860, 1636, 1640]}, 
                                 'Decagon': {'center_wavelengths_nm': [531, 532, 570, 830, 650, 800, 810]}}
                center_wavelengths_nm = [469, 530, 531, 532, 552, 570, 640, 644, 645, 650, 704, 740, 800, 810, 830, 856, 858, 860, 1636, 1640]
                    
                channels_df =  st.data_editor(
                    matched_channels, 
                    num_rows='fixed',
                    column_config={
                        'Down': st.column_config.SelectboxColumn('Down', required=True, options=matched_channels['Down']),
                        'sensor_model': st.column_config.SelectboxColumn('sensor_model', required=True, options=sensor_brands.keys()),
                        'center_wavelength_nm': st.column_config.SelectboxColumn('center_wavelength_nm', required=True, options=center_wavelengths_nm),
                        'sensor_sites_named': st.column_config.TextColumn('sensor_sites_named'),
                        'mast_height_m': st.column_config.NumberColumn('mast_height_m', min_value = 1.0, max_value=150.0, step=1.0)
                        }
                    )
                

                
        


    
    """

            
            
            
            confirm_btn =  dc1.button('confirm')

            if confirm_btn:
                st.session_state['confirm_source_data'] = True
            else:
                st.session_state['confirm_source_data'] = False

    # ---
    if confirm_btn and matched_channels is not None:
        

        

        st.write(channels_df.to_dict())
        """


        
if __name__ == 'calibrations_checks':
    run()
else:
    st.error('`calibrations_checks` failed initialization. Report issue to mantainers in github')