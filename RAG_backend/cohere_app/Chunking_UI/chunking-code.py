import os
import glob
import streamlit as st
import pandas as pd
from file_process import create_langchain_documents, ERROR_FOLDER
from pymilvus import connections, Collection
from pymilvus import MilvusClient
import logging
import enable_logging
import db_utility
from datetime import datetime

current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/{current_time}_logs.log")
    ],
)
logger = logging.getLogger(__name__)
## Process started  and completed symbol
chunking_monitor = db_utility.chunking_monitor()
if(chunking_monitor == False):
    logging.ERROR("Error found at creation of chunking monitor table")

## chunking_monitor insertion
chunking_monitor_insertion_query = f"""
    INSERT INTO chunking_monitor 
    (start_time, logging_file, chunked_folder, database)
    values
    ({current_time}, {current_time}_log.log, )
"""

client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus"
)
# connection and database table creation command
create_error_files_table = db_utility.create_error_files()

if(create_error_files_table == False):
    logging.error("Found error in creating error files table ")
    
def check(collection_name):
    connections.connect("default", host='localhost', port='19530')
    collection = Collection(collection_name)
    iterator = collection.query_iterator(batch_size=1000, output_fields=["source"])
    results = []
    while True:
        result = iterator.next()
        if not result:
            iterator.close()
            break
        results.extend(result)
    
    files_to_remove = list(set([result['source'] for result in results]))
    return files_to_remove

def find_files(root_dir, extensions):
    found_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for ext in extensions:
            for filepath in glob.glob(os.path.join(dirpath, '*' + ext)):
                found_files.append(filepath)
    return found_files

def connect_to_collection(collection_name, drop_or_append):
    collections = client.list_collections()
    if collection_name in collections:
        if drop_or_append == "Drop and recreate the collection":
            st.warning(f"Collection '{collection_name}' already exists. Dropping and recreating it.")
            client.drop_collection(collection_name=collection_name)
        else:
            st.success("No collection exists in name creating new collection.")
            st.info(f"Appending to the existing collection '{collection_name}'.")
    else:
        st.info(f"Creating new collection '{collection_name}'.")
    
    return collection_name

st.set_page_config(page_title="Document Chunking App", layout="wide")
st.title("AiCOE - Document Scraping")

collection_name = st.text_input("Enter the Milvus collection name:", value="")

if collection_name:
    drop_or_append = st.radio(
        "If the collection already exists, what do you want to do?",
        ("Append to existing collection", "Drop and recreate the collection")
    )
else:
    st.warning("Please provide a collection name before proceeding.")

if st.button("List All Collections"):
    try:
        collections = client.list_collections()
        st.write(f"Available collections: {collections}")
    except Exception as e:
        st.error(f"An error occurred while fetching collections: {e}")

st.subheader("Select source directory or input specific files to chunk")
source_folder = st.text_input("Enter the directory path to search for documents:", value="/home/llm/Desktop/oct_collection")

file_extensions = ['.pdf', '.txt', '.pptx', '.docx', '.xlsx', '.csv'] 
st.write(f"Supported formats: {', '.join(file_extensions)}")

manual_file_paths = st.text_area("Manually add file paths to chunk (one per line)")

progress_bar = st.progress(0)
progress_text = st.empty()
remaining_time_text = st.empty()

def update_progress(progress_percentage, remaining_time):
    progress_bar.progress(progress_percentage)
    progress_text.text(f"Progress: {progress_percentage}%")
    remaining_time_text.text(f"Estimated time remaining: {int(remaining_time // 60)} minutes {int(remaining_time % 60)} seconds")

if collection_name and st.button("Start Chunking"):
    if os.path.exists(source_folder) or manual_file_paths:
        st.write("Processing started. Please wait...")
        with st.spinner("Chunking documents..."):
            try:
                collection_name = connect_to_collection(collection_name, drop_or_append)

                if manual_file_paths:
                    file_list = manual_file_paths.split("\n")
                    file_list = [file.strip() for file in file_list if file.strip()]
                    create_langchain_documents(file_list, collection_name,update_progress_callback=update_progress)
                else:
                    found_files = find_files(source_folder, file_extensions)
                    already_chunked = []
                    if collection_name in client.list_collections():
                        already_chunked = check(collection_name)
                    needs_to_be_chunked = [item for item in found_files if item not in already_chunked]
                    if needs_to_be_chunked:
                        create_langchain_documents(needs_to_be_chunked, collection_name,update_progress_callback=update_progress)
                    else:
                        st.write("No new files need to be chunked.")
                st.success("Processing completed successfully!")
            except Exception as e:
                st.error(f"An error occurred during the processing: {e}")
    else:
        st.error("The specified directory or manual files do not exist. Please enter a valid directory or file paths.")
else:
    if not collection_name:
        st.warning("Please provide a collection name before starting chunking.")

st.subheader("Currently Processing Document")
processing_file = st.empty()
error_files = []
processed_files = []

st.subheader("Logs")
log_file = "Document Processing.log"
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        logs = f.read()
    st.text_area("Processing logs:", logs, height=400)
else:
    st.write("No logs available yet.")

st.subheader("Preview Available Files")

# Define how many files to show per page
files_per_page = 10

if os.path.exists(source_folder):
    found_files = find_files(source_folder, file_extensions)
    total_files = len(found_files)
    total_pages = (total_files // files_per_page) + 1 if total_files % files_per_page != 0 else total_files // files_per_page

    st.write(f"Found {total_files} files.")

    # Add a slider for pagination
    page_number = st.slider("Select page", 1, total_pages)

    # Calculate the start and end indices for the current page
    start_index = (page_number - 1) * files_per_page
    end_index = min(start_index + files_per_page, total_files)

    # Show files for the current page
    st.write(f"Displaying files {start_index + 1} to {end_index}:")
    for file in found_files[start_index:end_index]:
        st.write(file)

else:
    st.write("Please enter a valid directory to preview files.")


# st.subheader("Export Error Files from DB")
# if st.button("View Error Files in DB"):
#     connection = db_utility.create_connection()
#     cursor = connection.cursor()

#     df = pd.read_sql("SELECT * FROM error_files", connection)
#     st.write(df)

# if st.button("Export Error Files to CSV"):
#     connection = db_utility.create_connection()
#     cursor = connection.cursor()

#     df = pd.read_sql("SELECT * FROM error_files", connection)
#     csv_path = "error_files.csv"
#     df.to_csv(csv_path, index=False)
#     st.success(f"Error file locations exported to {csv_path}.")
#     st.download_button(label="Download CSV", data=open(csv_path, 'rb'), file_name=csv_path)
