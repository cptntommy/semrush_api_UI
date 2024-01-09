import requests
import pandas as pd
import streamlit as st
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import csv
import time

def make_api_request(api_key, database, keyword):
    url = "https://api.semrush.com/"
    params = {
        "type": "phrase_all",
        "key": api_key,
        "database": database,
        "phrase": keyword
    }
    with requests.Session() as session:
        response = session.get(url, params=params)
    return response.text.splitlines()

def query_semrush(api_key, database, keywords):
    results = []
    progress_bar = st.progress(0) #initialise progress bar
    total_keywords = len(keywords)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(make_api_request, api_key, database, keyword): keyword for keyword in keywords}
        for i, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            keyword = futures[future]
            lines = future.result()
            print(f"API Response for {keyword}: {lines}") #debug print
            data = csv.DictReader(lines, delimiter=";")
            for row in data:
                try:
                    search_volume = row["Search Volume"]
                    cpc = row["CPC"]  # Extract CPC data
                    date1 = row["Date"]
                    results.append(
                        {"Date": date1, "Database": database, "Keyword": keyword, "Search Volume": search_volume, "CPC": cpc})
                except KeyError as e:
                    print(f"KeyError for {keyword}: {e}") #debug print
                    continue
            progress_bar.progress(i / total_keywords) #update progress bar

    progress_bar.empty() #hide progress bar after completion
    print(f"Final Results: {results}")#debug print
    return pd.DataFrame(results)

# Streamlit app layout
st.title('SEMRush Keyword Search Volume Tool')

# Input for API key
api_key = st.text_input('Enter your SEMRush API key')

# Dropdown for database selection with an option for custom input
database_options = ['us', 'uk', 'ca', 'au', 'Other (Specify)']
selected_database = st.selectbox('Select the database', database_options)
# Conditional text input for custom database
if selected_database == 'Other (Specify)':
    custom_database = st.text_input('Enter the database name')
    st.write(
        "For a full database list, please visit the [documentation](https://developer.semrush.com/api/v3/analytics/basic-docs/#databases/)")
    database = custom_database.lower()  # Convert to lowercase as per your API requirement
else:
    database = selected_database.lower()  # Convert to lowercase

# Toggle between CSV upload and manual input
input_method = st.radio('Select your keyword input method', ('Upload CSV', 'Manual Input'))

if input_method == 'Upload CSV':
    uploaded_file = st.file_uploader('Upload your keyword list (CSV format)', type=['csv'])
    if uploaded_file is not None:
        keywords = pd.read_csv(uploaded_file, delimiter=',', on_bad_lines='warn')
else:
    keywords_text = st.text_area('Enter your keywords, separated by commas')
    if keywords_text:
        keywords = pd.DataFrame([keyword.strip() for keyword in keywords_text.split(',') if keyword], columns=['Keyword'])
    else:
        keywords = pd.DataFrame()

# Button to trigger the analysis
if st.button('Analyze Keywords'):
    if api_key and database and not keywords.empty:
        # Call your script logic here
        results = query_semrush(api_key, database, keywords['Keyword'])
        if isinstance(results, pd.DataFrame):
            st.write(results.head(10))  # Display only the first 10 rows
            # Add option to download results as CSV
            csv = results.to_csv(index=False)
            st.download_button('Download Full Results as CSV', csv, 'semrush_api_keywords.csv', 'text/csv')
        else:
            st.error('Error: ' + results)
    else:
        st.error('Please enter all required inputs.')
