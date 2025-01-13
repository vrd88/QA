import pandas as pd
import mysql.connector
from decouple import config
'''
Connection creation to MYSQL
'''
def create_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password= config("DATABASE_PASSWORD"),
        database=config("DATABASE_NAME")
    )
    return connection

'''
Error file related functions
'''
def create_error_files():
    connection = create_connection()
    cursor = connection.cursor()
    create_table_query = """
        CREATE TABLE IF NOT EXISTS error_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_path TEXT NOT NULL,
            error_message TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    cursor.execute(create_table_query)
    cursor.close()
    return True


def store_error_files_with_error(error_file_paths):
    connection = create_connection
    cursor = connection.cursor()
    cursor.executemany(
        "INSERT INTO error_files (file_path, error_message) VALUES (?, ?)",
        [(file_path, error_message) for file_path, error_message in error_file_paths]
    )
    connection.commit()
    cursor.close()

'''
User access table based function
'''
def create_user_access(collection_name):
    connection = create_connection()
    cursor = connection.cursor()
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS user_access_{collection_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        document_name TEXT,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        chunking_status ENUM('YES', 'NO') DEFAULT 'NO',
        message TEXT, 
        document_name_hash CHAR(64) AS (SHA2(document_name, 256)) VIRTUAL UNIQUE,
        INDEX idx_document_name_hash (document_name_hash)
    );
    '''
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    connection.close()
   

def fetch_all_documents(collection_name):
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Check if the table exists
        check_table_query = f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'SDC' AND table_name = 'user_access_{collection_name}';
        """
        cursor.execute(check_table_query)
        table_exists = cursor.fetchone()[0] > 0  # Returns True if the table exists

        if table_exists:
            # Query to select document_name from the table
            select_table_query = f'''
                SELECT document_name FROM user_access_{collection_name};
            '''
            cursor.execute(select_table_query)
            result = cursor.fetchall()
            document_names = [row[0] for row in result]
        else:
            document_names = []

        cursor.close()
        connection.close()
        return document_names

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def insert_user_access( document_source, chunking_status, message, collection_name):
    connection = create_connection()
    cursor = connection.cursor() 

    insert_query = f'''
    INSERT INTO user_access_{collection_name} (document_name, chunking_status, message) 
    VALUES (%s, %s, %s, %s);
    '''
    cursor.execute(insert_query, (document_source, chunking_status, message))
    connection.commit()


def chunking_monitor():
    """
    chunking_monitor Table related function
    """
    connection = create_connection()
    cursor = connection.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS chunking_monitor (
        id INT AUTO_INCREMENT PRIMARY KEY,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        completed_time TIMESTAMP NOT NULL,
        logging_file VARCHAR(255) NOT NULL,
        chunked_folder VARCHAR(255) NOT NULL,
        database_name VARCHAR(255) NOT NULL
    )
    '''
    cursor.execute(create_table_query)
    cursor.close()
    return True

def insert_chunking_monitor(query):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()
    return True

