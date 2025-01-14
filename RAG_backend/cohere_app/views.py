import PyPDF2
from io import BytesIO
from decouple import config
import os
from datetime import datetime, timedelta
import glob
import uuid
import subprocess
import urllib.parse
import threading
import mysql.connector
from pymilvus import connections, Collection, MilvusClient
from django.http import JsonResponse, StreamingHttpResponse, FileResponse, Http404
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import connection
from django.db.models import Min
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import PromptHistory, CurrentUsingCollection
from .serializers import PromptHistorySerializer, CurrentUsingCollectionSerializer
from .api import process_query, get_all_files_from_milvus,get_all_folders_from_milvus
from .Chunking_UI import file_process
from .Chunking_UI import enable_logging
from .Chunking_UI import db_utility 

# Initialize Milvus client
client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

# Global variable to store progress
progress_data = {"message": "Starting upload..."}

DEFAULT_PAGE_SIZE = 150
PDF_DIRECTORY = config('PDF_DIRECTORY')


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    try:
        user = authenticate(request, username=username, password=password)
    except Exception as e:
        print(f'Login error {e}')
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username
        })
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        # Get refresh token from request data
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        
        # Blacklist the refresh token
        token.blacklist()
        
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid token or logout failed"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cohere_generate(request):
    try:
        data = request.data
        prompt = data.get('prompt', '')
        session_id = data.get('session_id') or str(uuid.uuid4())
        file_names = data.get('file_names', [])
        jwt_token = data.get('jwt_token', '')
        # folder_path= data.get('selectedFolderPath', '')
        # folder_path= data.get('selectedFolderPath', '')
        
        # Print debug statements
        print('prompt:', prompt)
        print('jwt_token:', jwt_token)
        print('folder_path:',file_names)
        # print('folder_path:',folder_path)
# 
        # Create a placeholder PromptHistory entry
        prompt_history_entry = PromptHistory.objects.create(
            user=request.user,
            session_id=session_id,
            prompt=prompt,
            response=""
        )
        serializer = PromptHistorySerializer(prompt_history_entry)
        history_id = serializer.data['id']

        # Generator function for streaming response
        def response_stream():
            collected_responses = []

            # Stream partial responses from the process_query generator
            for partial_response in process_query(prompt, file_names, jwt_token):
                collected_responses.append(partial_response)

                yield partial_response

            # Combine all collected responses for final response
            combined_response = "\n".join(collected_responses)
            yield "      "  # Final padding chunk

            # Save the final response in the database (asynchronously in a separate thread)
            def save_to_database():
                prompt_history_entry.response = combined_response
                prompt_history_entry.save()

            threading.Thread(target=save_to_database).start()

        # Create the StreamingHttpResponse with headers for ID, session_id, file names, and page numbers
        response = StreamingHttpResponse(
            response_stream(),
            content_type='text/plain',
            status=status.HTTP_200_OK
        )
       

        # Add custom headers for file names, page numbers, history ID, and session ID
        response['X-History-ID'] = str(history_id)
        response['X-Session-ID'] = session_id
    
        # Set CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Expose-Headers'] = 'X-History-ID, X-Session-ID, X-File-Names, X-Page-Numbers'

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prompt_history(request):
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(weeks=1)
    last_month = today - timedelta(weeks=4)

    # Helper function to get first prompt per session for a given queryset
    def get_first_prompts(queryset):
        first_prompts = queryset.values('session_id').annotate(first_prompt_id=Min('id'))
        return PromptHistory.objects.filter(id__in=[fp['first_prompt_id'] for fp in first_prompts])

    # Filter by date ranges for the authenticated user
    user_prompts = PromptHistory.objects.filter(user=request.user)
    history_today = get_first_prompts(user_prompts.filter(created_at__date=today))
    history_yesterday = get_first_prompts(user_prompts.filter(created_at__date=yesterday))
    history_last_week = get_first_prompts(user_prompts.filter(created_at__gte=last_week, created_at__lt=yesterday))
    history_last_month = get_first_prompts(user_prompts.filter(created_at__gte=last_month, created_at__lt=last_week))

    # Serialize data
    history_data = {
        "today": PromptHistorySerializer(history_today.order_by('-created_at'), many=True).data,
        "yesterday": PromptHistorySerializer(history_yesterday.order_by('-created_at'), many=True).data,
        "last_week": PromptHistorySerializer(history_last_week.order_by('-created_at'), many=True).data,
        "last_month": PromptHistorySerializer(history_last_month.order_by('-created_at'), many=True).data
    }

    return Response(history_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_history(request, session_id):
   
    try:
        history = PromptHistory.objects.filter(user=request.user, session_id=session_id)
        if not history.exists():
            return Response({'error': 'No history found for this session'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PromptHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_comment(request, pk):
    try:
        # Retrieve the PromptHistory object by the primary key (id)
        prompt_history = PromptHistory.objects.get(pk=pk, user=request.user)
        comment = request.data.get('comments', '')

        if comment:
            # Save the comment if provided
            prompt_history.comments = comment
            prompt_history.save()
            return Response({"message": "Comment saved successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No comment provided"}, status=status.HTTP_204_NO_CONTENT)

    except PromptHistory.DoesNotExist:
        return Response({"error": "Prompt history not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_satisfied(request, pk):
    """
    Mark the feedback as satisfied.
    """
    try:
        # Retrieve the PromptHistory object by the primary key (id)
        prompt_history = PromptHistory.objects.get(pk=pk, user=request.user)
        
        # Update the thumbs_feedback column to 'satisfied'
        prompt_history.thumbs_feedback = 'satisfied'
        prompt_history.save()
        
        return Response({"message": "Feedback marked as satisfied."}, status=status.HTTP_200_OK)
    
    except PromptHistory.DoesNotExist:
        return Response({"error": "Prompt history not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_unsatisfied(request, pk):
    """
    Mark the feedback as unsatisfied.
    """
    try:
        # Retrieve the PromptHistory object by the primary key (id)
        prompt_history = PromptHistory.objects.get(pk=pk, user=request.user)
        
        # Update the thumbs_feedback column to 'unsatisfied'
        prompt_history.thumbs_feedback = 'unsatisfied'
        prompt_history.save()
        
        return Response({"message": "Feedback marked as unsatisfied."}, status=status.HTTP_200_OK)
    
    except PromptHistory.DoesNotExist:
        return Response({"error": "Prompt history not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_files(request):
    files = get_all_files_from_milvus()  
    return JsonResponse({"files":files}) 


@api_view(['GET'])
def get_documents(request):
    try:
        # Get the current collection name
        current_collection = CurrentUsingCollection.objects.first()  
        collection_name=current_collection.current_using_collection
        if not collection_name:
            return JsonResponse({'error': 'No current collection found'}, status=404)

        # Construct the table name dynamically
        table_name = f"user_access_{collection_name}"

        with connection.cursor() as cursor:
            # Execute the SQL query with the dynamically built table name
            query = f"SELECT document_name FROM {table_name}"
            cursor.execute(query)
            documents = cursor.fetchall()

        if documents:
            # Extract file names from the document paths
            file_names = [doc[0].split('/')[-1] for doc in documents]
            return JsonResponse({'files': file_names}, status=200)
        else:
            return JsonResponse({'error': 'No documents found for this ps_number'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def serve_pdf(request, filename, page_number):
    file_path = os.path.join(PDF_DIRECTORY, filename)
    
    try:
        if page_number < 1:
            raise ValueError("Page number must be greater than 0.")
    except ValueError:
        raise Http404("Invalid page number")
    
    # Check if the file exists
    if os.path.exists(file_path):
        # Open the PDF and extract the requested page
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            # Adjust for 0-based index in PyPDF2
            page_number -= 1 
            
            if page_number >= len(pdf_reader.pages):
                raise Http404("Page not found in PDF")

            # Create PDF writer to write the extracted page
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_number])

            # Create in-memory binary stream for the output PDF
            output_pdf = BytesIO()
            pdf_writer.write(output_pdf)
            output_pdf.seek(0)

            # Return the PDF as a response
            return FileResponse(output_pdf, content_type='application/pdf')
    else:
        raise Http404("PDF not found")


@api_view(['GET'])
def get_folder(request):
    folder = get_all_folders_from_milvus()  
    return JsonResponse({"folder":folder}) 


# admin page
@csrf_exempt  
def get_collection_name(request):
    try:
        # Connect to the Milvus server
        client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
        
        # List collections
        collections = client.list_collections()

        return JsonResponse({"collections": collections}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt  
def collection_files(request, collection_name):
    if request.method == 'GET':
        try:
            # Connect to Milvus
            connections.connect("default", host='localhost', port='19530')
            
            # Initialize collection object
            collection = Collection(collection_name)
            
            # Query the collection
            iterator = collection.query_iterator(batch_size=1000, output_fields=["source"])
            results = []
            
            while True:
                result = iterator.next()
                if not result:
                    iterator.close()
                    break
                results.extend(result)
            
            # Extract unique files using a set and convert back to a list
            results = list(set([result['source'] for result in results]))
            # Return the unique files as a JSON response
            return JsonResponse({"results": results}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt  
def delete_collection(request, collection_name):
    try:
        # Connect to Milvus
        client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
        
        # Delete the collection
        client.drop_collection(collection_name)
 # Step 2: Delete the corresponding table in MySQL
        connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Passw0rd@123",
        database="SDC"
    )
        cursor = connection.cursor()

        # Construct the table name
        table_name = f"user_access_{collection_name}"
        drop_table_query = f"DROP TABLE IF EXISTS `{table_name}`;"  # Use backticks for safety
        
        # Execute the query to drop the table
        cursor.execute(drop_table_query)
        connection.commit()
        cursor.close()
        connection.close()
        
        # Return success response
        return JsonResponse({"message": f"Collection '{collection_name}' deleted successfully."}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@api_view(['DELETE'])
def delete_file(request, source, collection_name):
    if request.method == 'DELETE':
        try:
           
            if not source or not collection_name:
                return JsonResponse({"error": "Both 'source' and 'collection_name' are required"}, status=400)

            # Connect to Milvus
            connections.connect("default", host='localhost', port='19530')

            # Access the collection
            collection = Collection(collection_name)
              # URL Decode the source (since it's URL-encoded)
            decoded_source = urllib.parse.unquote(source)
            print("Decoded source:", decoded_source)

            # Construct delete expression based on the provided source (file name)
            delete_expr = f"source == '{decoded_source}'" 
            # delete_expr = f"source LIKE '%{source}%'"

            # Perform the deletion
            result = collection.delete(expr=delete_expr)

            
            # Connect to MySQL to delete the corresponding row
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Passw0rd@123",
                database="SDC"
            )
            cursor = connection.cursor()

            # Construct the query to delete the row where document_name matches the source
            delete_row_query = f"DELETE FROM `user_access_{collection_name}` WHERE document_name = %s;"
            
            # Execute the query to delete the row
            cursor.execute(delete_row_query, (decoded_source,))
            connection.commit()
            cursor.close()
            connection.close()
            
            # Return success response
            if result.delete_count > 0:
                return JsonResponse({"message": f"All files with source '{source}' deleted successfully"}, status=200)
            else:
                return JsonResponse({"error": "No files found with the specified source name"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def set_progress_message(message):
    """
    Update the global progress message
    """
    global progress_data
    progress_data["message"] = message


# Helper function to find files in the source folder
def find_files(root_dir, extensions):
    found_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for ext in extensions:
            for filepath in glob.glob(os.path.join(dirpath, '*' + ext)):
                found_files.append(filepath)
    return found_files

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_collection(request):
    collection_name = request.data.get('name')
    source = request.data.get('source')
    if not collection_name or not source:
        return JsonResponse({"error": "Collection name and source are required."}, status=400)
    print(collection_name, source)
    try:
        enable_logging.logger.info(f"Starting collection creation for {collection_name}.")
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if the collection exists
        if collection_name in client.list_collections():
            enable_logging.logger.info(f"Collection {collection_name} already exists. Skipping creation.")
            set_progress_message(f"Collection {collection_name} already exists. Skipping creation.")
        else:
            enable_logging.logger.info(f"Creating new collection: {collection_name}")
        set_progress_message(f"Creating collection: {collection_name}")

        # Fetch already processed documents
        already_chunked = db_utility.fetch_all_documents(collection_name)
        enable_logging.logger.info(f"Already chunked documents: {already_chunked}")
        print("Hello",already_chunked)
        # Find files in the source directory
        file_extensions = ['.PDF', '.pdf', '.txt', '.pptx', '.docx', '.xlsx', '.csv']
        found_files = find_files(source, file_extensions)
        enable_logging.logger.info(f"Files found in source: {found_files}")

        # Filter files to determine what needs to be chunked
        needs_to_be_chunked = [file for file in found_files if file not in already_chunked]
        enable_logging.logger.info(f"Files needing chunking: {needs_to_be_chunked}")

        if needs_to_be_chunked:
            # Pass the file contents to create_langchain_documents and capture the progress
            progress_generator = file_process.create_langchain_documents(needs_to_be_chunked, collection_name)

            for progress in progress_generator:
                progress_message = f"Progress: {progress['current_progress']} Files completed / Total files{progress['total_files']} - {progress['progress_percentage']:.2f}%"
                set_progress_message(progress_message)
                print("progress_message:",progress_message)

        else:
            set_progress_message("No new files to process.")

        # Insert into chunking monitor
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insert_query_chunking_monitor = f"""
            INSERT INTO chunking_monitor (start_time, completed_time, logging_file, chunked_folder, database_name)
            VALUES ('{start_time}', '{end_time}', '{start_time}_logs.log','{collection_name}', '{source}')
        """
        db_utility.insert_chunking_monitor(insert_query_chunking_monitor)

        set_progress_message(f"Collection {collection_name} created successfully.")
        set_progress_message("Upload completed.")
        return JsonResponse({"message": "Collection creation completed."}, status=200)

    except Exception as e:
        enable_logging.logger.error(f"Error during collection creation: {str(e)}")
        set_progress_message(f"Error occurred: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


# Endpoint to get the current progress message
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress(request):
    return JsonResponse(progress_data)



@api_view(["GET"])
def get_milvus_data(request, collection_name):
    # Connect to Milvus
    connections.connect(alias="default", host="localhost", port="19530")
    
    # Fetch page and page size from request or set defaults
    page = int(request.GET.get("page", 1))  # Default to page 1
    page_size = DEFAULT_PAGE_SIZE

    try:
        # Load the collection
        collection = Collection(name=collection_name)
        collection.load()
    except Exception as e:
        return Response({"error": f"Failed to load collection: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Calculate offset
    offset = (page - 1) * page_size

    try:
        # Fetch data
        results = collection.query(
            expr="",  # Optional filter expression
            output_fields=["source", "page", "text", "pk"],
            offset=offset,
            limit=page_size,
        )

        if not results:
            return Response({"message": "No more data available"}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": f"Error querying Milvus: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Prepare response with pagination info
    response_data = {
        "data": results,
        "page": page,
        "page_size": page_size,
        "next_page": page + 1 if len(results) == page_size else None,  # Indicate the next page
    }

    return JsonResponse(response_data, safe=False)



@api_view(["GET"])
def get_current_using_collection(request):
    try:
        current_collection = CurrentUsingCollection.objects.first()  # Assuming there's only one record
        if current_collection:
            serializer = CurrentUsingCollectionSerializer(current_collection)
            return Response(serializer.data)
        else:
            return Response({"message": "No collection selected"}, status=404)
    except Exception as e:
        return Response({"error": f"Error fetching current collection: {str(e)}"}, status=500)


# cohere_app/views.py
from .globals import global_collection_name  # Import the global variable

@api_view(["POST"])
def update_current_collection(request):
    global global_collection_name  # Declare to modify the global variable

    # Get the selected collection from the request
    current_collection = request.data.get("current_using_collection")
    
    if not current_collection:
        return Response({"error": "No collection selected"}, status=400)

    # Update the CurrentUsingCollection table
    current_collection_instance, created = CurrentUsingCollection.objects.update_or_create(
        defaults={"current_using_collection": current_collection}
    )
    
    # Update the global variable with the new collection name
    global_collection_name = current_collection_instance.current_using_collection

    # Return success response
    return Response({
        "message": "Collection updated successfully", 
        "current_using_collection": global_collection_name
    }, status=200)



@csrf_exempt
def restart_server(request):
    if request.method == 'GET':
        try:
            subprocess.Popen(['python3', 'manage.py', 'runserver', '8000'])

            # Get the current process ID and kill it
            pid = os.getpid()
            os.kill(pid, 9)  # Kill the current process (SIGKILL)

            # os.execvp('python3', ['python3', 'manage.py', 'runserver', '8001'])

            return JsonResponse({'message': 'Server restarting...'})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Method not allowed'}, status=405)
