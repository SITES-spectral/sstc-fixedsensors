import os
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from dateutil import parser
import plotly.express as px


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


def raw_calibration_file_loader(
        delimeters:dict[str, str] = {'tab':'\t', 'comma':',', 'semicolon':';'}, 
        decimals:dict[str, str] = {'point':'.', 'comma':','}, 
        encodings:list[str] = ['utf-8', 'windows-1252'], 
        file_types:list[str] = ["dat", "csv", "txt", "tsv"]):
        
        uploaded_file_bytesio = st.file_uploader(
            label="Choose a calibration file:",
            type=file_types,)
        
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
                options=[0,1]
            )
            
        if delimeter and decimal and encoding:
            _delimeter = delimeters[delimeter]
            _decimal = decimals[decimal]


        if uploaded_file_bytesio is not None:
            df = pd.read_csv(
                uploaded_file_bytesio, 
                delimiter=_delimeter,
                decimal=_decimal,
                header=header,
                encoding=encoding)
            
            return df.drop(rows_with_xtra_headers, axis=0)


def harmonize_timestamp_column(df, timestamp_column):
    """
    Converts the TIMESTAMP column in a DataFrame to datetime format (YYYY-MM-DD HH:MM:SS).

    Parameters:
    df (pd.DataFrame): DataFrame containing the TIMESTAMP column.
    timestamp_column (str): Name of the column containing the timestamps.

    Returns:
    pd.DataFrame: DataFrame with the TIMESTAMP column converted to datetime format.
    """
    # Function to parse and format the datetime
    def parse_and_format(timestamp):
        try:
            return parser.parse(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return None
    
    # Apply the function to the timestamp column
    df[timestamp_column] = df[timestamp_column].apply(parse_and_format)
    
    # Convert the column to datetime dtype
    df[timestamp_column] = pd.to_datetime(df[timestamp_column], errors='coerce')
    
    return df
                
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


def match_up_with_dw(updown_channels:list, prefix_up = "Up", prefix_down = "Dw", split_on = '_' ):
    # Create dictionaries to hold the Up and Dw values
    up_dict = {}
    dw_dict = {}

    # Separate the Up and Dw values into their respective dictionaries
    for item in updown_channels:
        if item.startswith(prefix_up):
            key = item.split(split_on)[1]
            up_dict[key] = item
        elif item.startswith(prefix_down):
            key = item.split(split_on)[1]
            if key not in dw_dict:
                dw_dict[key] = []
            dw_dict[key].append(item)
    
    # Create a result dictionary to match Up with corresponding Dw values
    result = {}
    for key in up_dict:
        if key in dw_dict:
            result[up_dict[key]] = dw_dict[key]
    
    return result

def ensure_continuous_timeseries(df, time_column='TIMESTAMP', freq='5S'):
    """
    Ensures a continuous time series for the given DataFrame by filling missing timestamps.
    
    Parameters:
    df (pd.DataFrame): Input DataFrame.
    time_column (str): The name of the timestamp column.
    freq (str): Frequency string to specify the interval for the time series (default is '5S' for 5 seconds).
    
    Returns:
    pd.DataFrame: DataFrame with a continuous time series.
    """
    # Ensure the time_column is a datetime type
    df[time_column] = pd.to_datetime(df[time_column])
    
    # Set the time_column as the index
    df.set_index(time_column, inplace=True)
    
    # Create a complete date range with the specified frequency
    complete_time_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    
    # Reindex the DataFrame to the complete date range, filling missing values with None
    df = df.reindex(complete_time_index).reset_index()
    
    # Rename the index column back to the time_column name
    df.rename(columns={'index': time_column}, inplace=True)
    
    return df


# Function to create the interactive plot
def create_plot(df, y_axis, timestamp_col = 'TIMESTAMP' ):
    fig = px.scatter(df, x=timestamp_col, y=y_axis, title=f'Time Series of {y_axis}')
    fig.update_traces(mode='markers')
    fig.update_layout(
        xaxis_title=timestamp_col,
        yaxis_title=y_axis,
        showlegend=False
    )
    fig.update_xaxes(rangeslider_visible=True)
    return fig

def run(
        timestamp_col:str = 'TIMESTAMP', 
        common_columns:list[str] = [
                'TIMESTAMP', 
                'RECORD',
                'BattV_Min',
                'PTemp_C_Avg',
                'Temp_Avg',
                'Temp',
                'PTemp',
                'var1',
                'Var1',
                ] ):
            
    show_matched_channels = False
    
    with st.expander('**Step 01**: Load calibration dataset and pre-screening', expanded=True):
        if st.sidebar.button('Instructions'):
            show_instructions_dialog()
        # Step 01
        df = raw_calibration_file_loader()

        # Step 02
        if df is not None and isinstance(df, pd.DataFrame):
            if timestamp_col in df.columns:
                df =  harmonize_timestamp_column(df, timestamp_col)
        
            editor_df = st.data_editor(df, num_rows='dynamic', hide_index=False)
            show_matched_channels = True
        else:
            show_matched_channels = False
        
    if show_matched_channels:
        with st.expander('**Step 02**: Updown channels matching'):
                
            columns = list(df.columns)
            updown_channels = [c for c in columns if c not in common_columns]
            matched_channels = match_up_with_dw(updown_channels=updown_channels,
                                prefix_up="Up",
                                prefix_down="Dw",
                                split_on='_')

            st.write(matched_channels)
        with st.expander('**Step 03** channels data plots'):
            st.title('Interactive Time Series Plot')

            # Dropdown menu to select the Y-axis column
            y_axis = st.selectbox('Select Y-axis column', updown_channels)

            # Create and display the plot
            fig = create_plot(editor_df, y_axis, timestamp_col=timestamp_col)
            st.plotly_chart(fig, use_container_width=True)
        
            """
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
                                st.toast('Ready to **Step 04**')'
                                """

if __name__=="ui_post_calibration":
    run()