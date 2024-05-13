import streamlit as st
import pandas as pd
from io import StringIO


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
    
if uploaded_file is not None:

    if 'delete_rows' not in st.session_state:
        st.session_state['delete_rows'] = []
    

    with st.expander('Calibration source data', expanded=True):
        dc1, dc2 = st.columns([1,3])
        with dc1:
            delete_rows = st.multiselect(
            label='extra headers rows to **delete**:',
            options=[0,1,2,3,4],
            )

                        
        with dc2:
            df = sstc_read_csv(
                uploaded_file,
                header=1, 
                delete_rows=delete_rows)
            
            
            st.write(df)

        confirm_btn =  dc1.button('confirm')

        if confirm_btn:
            st.session_state['confirm_source_data'] = True
        else:
            st.session_state['confirm_source_data'] = False
            


