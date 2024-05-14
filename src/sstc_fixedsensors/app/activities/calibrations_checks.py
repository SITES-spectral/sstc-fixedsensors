import streamlit as st
import pandas as pd
from calval import calibration

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


col1, col2 = st.columns([1,1])

with col1:
    with st.expander(label='**Instructions**', expanded=True):            
        st.info("1) Drag and drop (or browse file)  **logged calibration** data file to quick check calibration.")
        st.info("2) Check that data has the right format")
        st.info("3) Select extra header rows to be deleted to keep the data clean")

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
    


    