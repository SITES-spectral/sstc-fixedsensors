import streamlit as st
import pandas as pd

from schemas import SITES
import requests

import numpy as np
from scipy.optimize import curve_fit

import uuid
from datetime import datetime

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

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode("utf-8")

def generate_filename(station:str, name:str ):
    # Generate a global unique ID
    unique_id = uuid.uuid4()
    
    # Get the current date and time
    now = datetime.now()
    
    # Format date and time as a string with no spaces or special characters
    date_time_str = now.strftime("%Y-%m-%dT%H%M%S")
    
    # Combine all parts to form the final string
    filename = f"{date_time_str}_{station}_{name}_{unique_id}.dat"
    
    return filename

def linear_fit(x, a, b):
    return a * x + b

def calibration(
        up_channel: pd.Series, 
        dw_channel:pd.Series, 
        standard=1, 
        Threshold=0.03, 
        Iter=100, 
        speed=6):
    
    if len(up_channel) != len(dw_channel):
        print('Must be two equal length arrays')
        return
    
    dw_channel = dw_channel / standard
    XX, YY = up_channel.copy(), dw_channel.copy()

    popt, _ = curve_fit(linear_fit, up_channel, dw_channel)
    yfit = linear_fit(up_channel, *popt)
    ME = np.abs((yfit - dw_channel) / yfit)
    MaxME = np.max(ME)
    counter = 0
    
    while MaxME > Threshold:
        Ind = np.where(ME > speed * Threshold)[0]
        up_channel = np.delete(up_channel, Ind)
        dw_channel = np.delete(dw_channel, Ind)
        
        popt, _ = curve_fit(linear_fit, up_channel, dw_channel)
        yfit = linear_fit(up_channel, *popt)
        ME = np.abs(yfit - dw_channel) / np.mean(yfit)
        MaxME = np.max(ME)
        speed -= 1
        if speed < 1:
            speed = 1
        counter += 1
        print('Iteration {}, Wait...'.format(counter))
        if counter > Iter:
            print('Reach maximum iteration!')
            return
    
    print('Samples left {}.'.format(len(up_channel)))
    
    # Return the necessary data for plotting
    return XX, YY, up_channel, dw_channel, yfit



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
    
    if 'station' not in st.session_state:
        st.session_state['station'] = 'SSTC'
    if 'columns' not in st.session_state:
        st.session_state.columns = []

    if 'all_channels' not in st.session_state:
        st.session_state.all_channels = None
    if 'delete_rows' not in st.session_state:
        st.session_state.delete_rows = []
        
    if 'is_step01_done' not in st.session_state:
        st.session_state['is_step01_done'] = False
    if 'is_step02_done' not in st.session_state:
        st.session_state['is_step02_done'] = False
    if 'is_step03_done' not in st.session_state:
        st.session_state['is_step03_done'] = False
    if 'is_step04_done' not in st.session_state:
        st.session_state['is_step04_done'] = False
    if 'is_sensor_calibration_done' not in st.session_state:
        st.session_state['is_sensor_calibration_done'] = False
    if 'calibration_df' not in st.session_state:
        st.session_state['calibration_df'] = None
    if 'cal_df' not in st.session_state:
        st.session_state.cal_df = pd.DataFrame({'dummy': []})
    if 'channels_df' not in st.session_state:
        st.session_state.channels_df = pd.DataFrame({'dummy': []})

def station_selectbox()->str:
    research_stations =  st.session_state['research_stations']
    station = st.selectbox(
        'Choose your Station:',
        options=research_stations.keys()
        )
    st.session_state['station'] = station
    return station


@st.experimental_dialog('Instructions')
def show_instructions_dialog():
    load_instructions()
    

@st.experimental_dialog('calibration dataset')
def show_raw_calibration(raw_calibration_df:pd.DataFrame):
    if raw_calibration_df is not None:
        st.write(raw_calibration_df)

def step01():
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

        if calibration_df is not None:
            st.session_state.calibration_df = calibration_df
            
            st.session_state.is_step01_done = True

            columns = list(calibration_df.columns)
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
            st.session_state.all_channels = all_channels
            st.session_state.columns = columns

        else:
            st.session_state.calibration_df = None
            st.session_state.is_step01_done = False
            st.session_state.all_channels = None

def step02():
    cal_df = st.session_state['calibration_df']
    timestamp_col = None
    message = st.empty()
    # ---

    step02_col1, step02_col2 = st.columns([1,5], gap='small')

    with step02_col1:
        delete_rows = st.multiselect(
            label='**delete** row number:',
            options=[0,1],
            )
        st.session_state['delete_rows']= delete_rows

    with step02_col2:
        st_cal = st.empty()

        cal_df = cal_df.drop(st.session_state['delete_rows'], axis=0)
        if 'TIMESTAMP' in st.session_state.columns:
            try:                        
                timestamp_col = 'TIMESTAMP'
                cal_df[timestamp_col] = pd.to_datetime(
                    cal_df['TIMESTAMP'],
                    format='%Y-%m-%d %H:%M:%S'
                    ) 

            except:
                message.error('`TIMESTAMP` cannot be processed. Delete extra rows affecting data values.')
                st_cal = st.dataframe(cal_df)
                st.session_state.is_step02_done = False 
            else:
                
                none_indices = [int(i) for i in  cal_df.loc[cal_df[timestamp_col].isna()].index]
                
                st.dataframe(cal_df)
                
                if len(none_indices) >0:
                    #st_cal.dataframe(cal_df)
                    message.warning(f'Please remove the rows where `TIMESTAMP` is empty: rows {none_indices}')
                    st.session_state.is_step02_done = False
                else:                                                   
                    message.success('`TIMESTAMP` recognized. Continue to **STEP 03**')
                    #st_cal.dataframe(cal_df)
                    st.session_state.cal_df = cal_df
                    st.session_state.is_step02_done = True
        else:
            message.error('`TIMESTAMP` column not found')
            st.session_state.is_step02_done = False
        

def run():
    initialize()

    _, instructions_col1, header_stations_col = st.columns([1,2,2], gap='small')
    station = None
    with instructions_col1:
        with st.container(border=True):
            if st.button('Instructions'):
                show_instructions_dialog()
                
        with header_stations_col:
            station = station_selectbox()
            st.session_state.station = station


    with st.expander('**Step 01**: Load calibration dataset', expanded=True):
        step01()    

    if st.session_state.is_step01_done:            
        with st.expander('**STEP 02**: dataprep'):
            step02()

            # Remove rows where there is no value in a subset of columns (Column1 and Column2)
            #cal_df_cleaned = cal_df.dropna(subset=st.session_state.all_channels)
            #number_of_missing_data = len(cal_df) - len(cal_df_cleaned)
            #if len(number_of_missing_data >0):
            #    message.warning(f'Detected {number_of_missing_data} `empty` values in channels. Autoremove rows in progress')
            #    cal_df = cal_df_cleaned
                                                    
    if st.session_state.is_step02_done:
        with st.expander('**STEP 03**: Revise channels pairs and center wavelengths for each channel'):
            
            # split the column names and select the first item in the list which is expected to be `Up` or `Dw`.
            up_channels = pd.DataFrame.from_dict({
                'Up': [u for u in st.session_state.all_channels if u.split(sep='_')[0] in ['Up', 'up'] ]})
        
            down_channels = pd.DataFrame.from_dict({'Down': [d for d in st.session_state.all_channels if  d.split(sep='_')[0] in ['Dw', 'dw'] ]})
        
            matched_channels = pd.concat([up_channels, down_channels], axis=1)
            matched_channels['sensor_model'] = None

            matched_channels['sensor_sites_named'] = None            
            matched_channels['center_wavelength_nm'] = None
            matched_channels['mast_height_m'] = None
            matched_channels['is_validated'] = False

            if matched_channels is not None:
                sensor_brands = {'Skye': {'center_wavelengths_nm': [469, 530, 531, 532, 552, 570, 640, 644, 645, 650, 704, 740, 810, 856, 858, 860, 1636, 1640]}, 
                                'Decagon': {'center_wavelengths_nm': [531, 532, 570, 830, 650, 800, 810]}}
                center_wavelengths_nm = [469, 530, 531, 532, 552, 570, 640, 644, 645, 650, 704, 740, 800, 810, 830, 856, 858, 860, 1636, 1640]
                    
                channels_df =  st.data_editor(
                    key='matched_channels_data_editor',
                    data=matched_channels, 
                    num_rows='fixed',
                    column_config={
                        'Down': st.column_config.SelectboxColumn('Down', required=True, options=matched_channels['Down']),
                        'sensor_model': st.column_config.SelectboxColumn('sensor_model', required=True, options=sensor_brands.keys()),
                        'center_wavelength_nm': st.column_config.SelectboxColumn('center_wavelength_nm', required=True, options=center_wavelengths_nm),                        
                        'mast_height_m': st.column_config.NumberColumn('mast_height_m', min_value = 1.0, max_value=150.0, step=0.5)
                        }
                    )
                
                if channels_df is not None:
                    st.session_state.channels_df = channels_df
                    st.session_state.is_step03_done = True
                    c1, c2 = st.columns([1,1])
                    with c1:
                        sensor_type = st.text_input('sensor_type', placeholder='SN54105')
                    

                    filename = generate_filename(
                        station=st.session_state.station,
                        name=f'sensor_{sensor_type if len(sensor_type)>0 else "type" }_channels_configuration'
                    )

                    with c2:
                        st.write('**filename:**')
                        st.write(f'**{filename}**')

                        if st.download_button(
                            '**download file**',
                            data= convert_df(channels_df),
                            file_name=filename
                            ):
                            st.session_state.is_step03_done = True
                            st.toast('Ready to **Step 04**')

        with st.expander("**STEP 04**: calibration plot"):
            up_channel = st.session_state.cal_df[ st.session_state.channels_df.loc[0, 'Up']].astype(float)  #.apply(lambda x: float(x))
            dw_channel = st.session_state.cal_df[ st.session_state.channels_df.loc[0, 'Down']].astype(float)  #.apply(lambda x: float(x))            

            if len(up_channel) != len(dw_channel):
                st.error('`up_channel` and `down_channel` must have equal lengths')
                st.stop()
            else:
                #standard=1, 
                #Threshold=0.03, 
                #Iter=100, 
                #speed=6

                # Perform calibration
                XX, YY, up_channel_calibrated, dw_channel_calibrated, yfit = calibration(up_channel, dw_channel)

                # Plot using Streamlit
                st.line_chart(pd.DataFrame({'XX': XX, 'YY': YY, 'up_channel_calibrated': up_channel_calibrated, 
                                        'dw_channel_calibrated': dw_channel_calibrated, 'yfit': yfit}))

                
        
if __name__ == 'calibrations_checks':
    run()
else:
    st.error('`calibrations_checks` failed initialization. Report issue to mantainers in github')