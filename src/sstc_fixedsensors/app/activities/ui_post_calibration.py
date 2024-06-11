import os
import streamlit as st
import pandas as pd


def timestamp_column_check(
        df:pd.DataFrame, 
        timestamp_col: str = 'TIMESTAMP',
        format='%Y-%m-%d %H:%M:%S'
        ):

    df[timestamp_col] = pd.to_datetime(
        df[timestamp_col],
        format=format
        )
    return df


def step02_postcalibration_check(
        df:pd.DataFrame, 
        timestamp_col: str = 'TIMESTAMP',
        do_not_include_columns = [
                'TIMESTAMP', 
                'RECORD',
                'BattV_Min',
                'PTemp_C_Avg',
                'Temp_Avg',
                'Temp',
                'PTemp',
                ],    ):
    
    columns = list(df.columns)
    all_channels = [c for c in columns if c not in do_not_include_columns]
    st.session_state['METADATA']['all_channels'] = all_channels
    timestamp_col = None
    message = st.empty()
    step02_col1, step02_col2 = st.columns([1,5], gap='small')

    with step02_col1:
        deleted_rows = st.multiselect(
            label='**delete** extra headers:',
            options=[0,1],
            help='select those **rows numbers with extra headers to be deleted**',
            )
        st.session_state['METADATA']['rows_with_extra_headers_deleted']= deleted_rows

    with step02_col2:

        cal_df = df.drop(st.session_state['METADATA']['rows_with_extra_headers_deleted'], axis=0)
        if 'TIMESTAMP' in cal_df.columns:
            try:                        
                timestamp_col = 'TIMESTAMP'
                cal_df[timestamp_col] = pd.to_datetime(
                    cal_df['TIMESTAMP'],
                    format='%Y-%m-%d %H:%M:%S'
                    ) 

            except:
                message.sidebar.error('`TIMESTAMP` cannot be processed. Delete extra rows affecting data values.')
                
                
            else:
                
                none_indices = [int(i) for i in  cal_df.loc[cal_df[timestamp_col].isna()].index]
                
                
                if len(none_indices) >0:
                    #st_cal.dataframe(cal_df)
                    message.sidebar.warning(f'Please remove the rows where `TIMESTAMP` is empty: rows {none_indices}')
                    st.session_state['METADATA']['is_step02_done'] = False
                else:                                                   
                    message.sidebar.success('`TIMESTAMP` recognized. Ready for post-calibration evaluation')
                    
                    st.session_state['METADATA']['is_step02_done'] = True
                
                return cal_df
        else:
            message.sidear.error('`TIMESTAMP` column not found')
            st.session_state['METADATA']['is_step02_done'] = False




def raw_calibration_file_loader(
        delimeters:dict[str, str] = {'tab':'\t', 'comma':',', 'semicolon':';'}, 
        decimals:dict[str, str] = {'point':'.', 'comma':','}, 
        encodings:list[str] = ['utf-8', 'windows-1252'], 
        file_types:list[str] = ["dat", "csv", "txt", "tsv"],
        timestamp_col: str = 'TIMESTAMP',
        do_not_include_columns = [
                'TIMESTAMP', 
                'RECORD',
                'BattV_Min',
                'PTemp_C_Avg',
                'Temp_Avg',
                'Temp',
                'PTemp',
                ],
        
        ):
        
        uploaded_file_bytesio = st.file_uploader(
            label="Choose a calibration file:",
            type=file_types,
            
            )
        
        col_delimiter, col_decimal, col_encoding, col_header_row, col_delete_xtra_headers  = st.columns([1,1,1,1,1])
                    
        with col_delimiter:
            delimeter = st.selectbox(label='**delimeter:**', options=delimeters)
        with col_decimal:
            decimal = st.selectbox(label='**decimal:**', options=decimals)
        with col_encoding:
            encoding = st.selectbox(label='**encoding:**', options=encodings)
        with col_header_row:
            header = st.number_input(
                label="**header row**",
                min_value=0,
                max_value=3,
                value=1
            )
        with col_delete_xtra_headers:
            rows_with_xtra_headers = st.multiselect(
                label='**rows with extra-headers**',
                help='select the rows (to be deleted) that contain extra headers',
                options=[0,1,2],

            )
            st.session_state['METADATA']['rows_with_extra_headers_deleted']= rows_with_xtra_headers

    
        if delimeter and decimal and encoding:
            _delimeter = delimeters[delimeter]
            _decimal = decimals[decimal]


        if uploaded_file_bytesio is not None:
            df = pd.read_csv(
                uploaded_file_bytesio, 
                delimiter=_delimeter,
                decimal=_decimal,
                header=header,
                encoding=encoding,
                        
                )
        else:
            df = None

        
        if df is not None:
            columns = list(df.columns)
            all_channels = [c for c in columns if c not in do_not_include_columns]
            st.session_state['METADATA']['all_channels'] = all_channels
            timestamp_col = None
            message = st.empty()
            cal_df = df.drop(st.session_state['METADATA']['rows_with_extra_headers_deleted'], axis=0)
      
            if 'TIMESTAMP' in cal_df.columns:
                try:                        
                    timestamp_col = 'TIMESTAMP'
                    cal_df[timestamp_col] = pd.to_datetime(
                        cal_df['TIMESTAMP'],
                        format='%Y-%m-%d %H:%M:%S'
                        ) 

                except:
                    message.error('`TIMESTAMP` cannot be processed. Delete extra rows affecting data values.')
                else:
                    none_indices = [int(i) for i in  cal_df.loc[cal_df[timestamp_col].isna()].index]

                    if len(none_indices) >0:
                        
                        message.warning(f'Please remove the rows where `TIMESTAMP` is empty: rows {none_indices}')
                        st.session_state['METADATA']['is_step02_done'] = False
                    else:                                                   
                        message.success('`TIMESTAMP` recognized. Ready for post-calibration evaluation')
                        
                        st.session_state['METADATA']['is_step02_done'] = True
                    
                
            else:
                message.sidear.error('`TIMESTAMP` column not found')
                st.session_state['METADATA']['is_step02_done'] = False
            
            return cal_df

@st.cache_data()
def load_instructions():

    file_path = st.session_state['APP']['INSTRUCIONS_FILEPATH']

    if not isinstance(file_path, str):
        return "Error: The file path must be a string."
    
    if not os.path.isfile(file_path):
        return f"Error: The file '{file_path}' does not exist."

    if not file_path.lower().endswith('.md'):
        return "Error: The file is not a Markdown file."

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except Exception as e:
        return f"Error: An error occurred while reading the file. Details: {e}"


@st.experimental_dialog('Instructions')
def show_instructions_dialog():
    content = load_instructions()
    if content is not None:
        st.markdown(content)                
        


def run():        

    with st.expander('**Step 01**: Load calibration dataset and pre-screening', expanded=True):
        if st.sidebar.button('Instructions'):
            show_instructions_dialog()

       
        # Step 01
        df = raw_calibration_file_loader()

        st_editor = st.empty()
        # Step 02
        if df is not None and isinstance(df, pd.DataFrame):
            data_editor = st.data_editor(df, num_rows='dynamic')
        
        
                
        
            



if __name__=="ui_post_calibration":
    run()