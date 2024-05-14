import streamlit as st
import pandas as pd
from calval import calibration
from schemas import SITES
import os

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

@st.cache_data()
def load_instructions():
    working_directory = st.session_state.get('working_directory', None)
    with open(os.path.join(working_directory, "instructions.md"), 'r') as markdown_file:
        markdown_text = markdown_file.read()
    st.markdown(markdown_text)
    

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
    data = pd.read_csv(
        uploaded_file, 
        delimiter=',',
        decimal='.',
        header=header,
        encoding='utf-8',        
        )
    
    _to_delete = []

    for i in data.index:
        if int(i) in delete_rows:
            _to_delete.append(i)
    
    data.drop(_to_delete, inplace=True)

    return data

@st.experimental_dialog('Instructions')
def show_instructions_dialog():
    load_instructions()


def run():
    initialize()

    instructions_col1, header_col2, header_col3 = st.columns([2,1,1])

    with instructions_col1:
        if st.button('Instructions'):
            show_instructions_dialog()


    with header_col3:
        station = station_selectbox()
    st.divider()
        

    col1, col2 = st.columns([1,1])

    with col1:
        pass
    with col2:
        uploaded_file = st.file_uploader(
            label="Choose a calibration file:",
            type=["dat", "csv", "txt", "tsv"])

    # ----
    confirm_btn = False

    if uploaded_file is not None:

        if 'delete_rows' not in st.session_state:
            st.session_state['delete_rows'] = []
        

        with st.expander('Calibration source data', expanded=True):
            dc1, dc2 = st.columns([1,3])
            with dc1:
                delete_rows = st.multiselect(
                label='extra headers rows to **delete**:',
                options=[0,1,2],
                )
            with dc2:
                df = sstc_read_csv(
                    uploaded_file,
                    header=1, 
                    delete_rows=delete_rows)
                
                columns = list(df.columns)
                st.write(df)

            with dc1:
                timestamp_col = None
                if 'TIMESTAMP' in columns:
                    try:                        
                        timestamp_col = 'TIMESTAMP'
                        df[timestamp_col] = pd.to_datetime(df['TIMESTAMP'])
                        #if df['timestamp_col'].loc[0] is not None:
                        st.success('`TIMESTAMP` recognized. Ensure no extra rows as headers affecting other values. Remove rows if necesary.')
                    except:
                        st.error('`TIMESTAMP` cannot be processed. Delete extra headers affecting values.')
                else:
                    st.warning('`TIMESTAMP` column not found')

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
                up_channels = pd.DataFrame.from_dict({'Up': [u for u in all_channels if u.split(sep='_')[0] in ['Up', 'up'] ]})
                down_channels = pd.DataFrame.from_dict({'Down': [d for d in all_channels if  d.split(sep='_')[0] in ['Dw', 'dw'] ]})
                
                matched_channels = pd.concat([up_channels, down_channels], axis=1)
                
                
                confirm_btn =  dc1.button('confirm')

                if confirm_btn:
                    st.session_state['confirm_source_data'] = True
                else:
                    st.session_state['confirm_source_data'] = False

    # ---
    if confirm_btn and matched_channels is not None:
        

        channels_df =  st.data_editor(
            matched_channels, 
            num_rows='fixed',
            column_config={'Down': st.column_config.SelectboxColumn('Down', required=True, options=matched_channels['Down'])}
            )

        st.write(channels_df.to_dict())
        


        
if __name__ == 'calibrations_checks':
    run()
else:
    st.error('`calibrations_checks` failed initialization. Report issue to mantainers in github')