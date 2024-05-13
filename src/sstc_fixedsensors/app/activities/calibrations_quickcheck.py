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
        infer_datetime_format=True,             
        )
    
    _to_delete = []

    for i in data.index:
        if int(i) in delete_rows:
            _to_delete.append(i)
    
    data.drop(_to_delete, inplace=True)

    return data


col1, col2 = st.columns([1,1])

with col1:
    uploaded_file = st.file_uploader(
        label="Choose a calibration file:",
        type=["dat", "csv", "txt", "tsv"])
    
with col2:
    delete_rows = st.multiselect(
        label='metadata rows to delete:',
        options=[0,1,2,3,4],
        )

if uploaded_file is not None:
    
    df = sstc_read_csv(
        uploaded_file,
        header=1, 
        delete_rows=delete_rows)
    
    st.write(df)