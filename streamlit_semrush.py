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

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(make_api_request, api_key, database, keyword): keyword for keyword in keywords}
        for future in concurrent.futures.as_completed(futures):
            keyword = futures[future]
            lines = future.result()
            print(f"API Response for {keyword}: {lines}")  # Debug print
            data = csv.DictReader(lines, delimiter=";")
            for row in data:
                try:
                    search_volume = row["Search Volume"]
                    date1 = row["Date"]
                    results.append(
                        {"Date": date1, "Database": database, "Keyword": keyword, "Search Volume": search_volume})
                except KeyError as e:
                    print(f"KeyError for {keyword}: {e}")  # Debug print
                    continue

    print(f"Final Results: {results}")  # Debug print
    return pd.DataFrame(results)



# Streamlit app layout
st.title('SEMRush Keyword Analysis Tool')

# Input for API key
api_key = st.text_input('Enter your SEMRush API key')

# Input for database selection
database = st.selectbox('Select the database', ['us', 'uk', 'ca', 'au'])  # Update as per your script's capabilities

# Toggle between CSV upload and manual input
input_method = st.radio('Select your keyword input method', ('Upload CSV', 'Manual Input'))

if input_method == 'Upload CSV':
    uploaded_file = st.file_uploader('Upload your keyword list (CSV format)', type=['csv'])
    if uploaded_file is not None:
        keywords = pd.read_csv(uploaded_file)
else:
    keywords_text = st.text_area('Enter your keywords, separated by commas')
    keywords = [keyword.strip() for keyword in keywords_text.split(',') if keyword]

# Button to trigger the analysis
if st.button('Analyze Keywords'):
    if api_key and database and keywords:
        # Call your script logic here
        results = query_semrush(api_key, database, keywords)
        if isinstance(results, pd.DataFrame):
            st.write(results)  # Display the results as a table
            # Add option to download results as CSV
            csv = results.to_csv(index=False)
            st.download_button('Download Results as CSV', csv, 'keywords_analysis.csv', 'text/csv')
        else:
            st.error('Error: ' + results)
    else:
        st.error('Please enter all required inputs.')

# Run this with `streamlit run your_script_name.py`
