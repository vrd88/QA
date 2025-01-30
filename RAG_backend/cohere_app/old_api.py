from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from functools import lru_cache 
from pymilvus import connections, Collection
import os
from .globals import global_collection_name
from .models import CurrentUsingCollection
import re
from langchain_groq import ChatGroq
import time

def generate_response(prompt: str):

    api_keys = [
    "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",
    "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",
    ]

    # Initialize ChatGroq parameters
    model_name = "llama-3.3-70b-versatile"

    for api_key in api_keys:
        try:
            llm = ChatGroq(model_name=model_name, api_key=api_key)
            messages = [
                (
                    "system",
                    "You are a helpful assistant.",
                ),
                ("human", f"{prompt}"),
            ]
            ai_msg = llm.invoke(messages)
            return ai_msg.content
        except Exception as e:
            time.sleep(1)

    # If all keys fail
    raise Exception("All API keys have failed. Please check your API keys or service status.")

MILVUS_COLLECTION = 'QC_Collection'

def get_current_using_collection_value():
    try:
        current_collection = CurrentUsingCollection.objects.first()  
        if current_collection:
            # Assign the collection name to a variable
            collection_name = current_collection.current_using_collection
            return str(collection_name)
        else:
            return None 
    except Exception as e:
        return str(e) 

collection_name = get_current_using_collection_value()

if collection_name:
    MILVUS_COLLECTION = collection_name

#TODO - remove this
MILVUS_COLLECTION = 'QC_Collection'


connections.connect("default", host="localhost", port="19530")
collection = Collection(MILVUS_COLLECTION)
collection.load()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_string(input_string):
    cleaned_string = re.sub(r'\s+', ' ', input_string)
    cleaned_string = cleaned_string.strip()
    return cleaned_string

# def generate_streaming_response(input_text):
#     inputs = tokenizer(input_text, return_tensors="pt").to(device)
#     streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
#     thread = Thread(target=model.generate,
#                     kwargs={
#                         "input_ids": inputs['input_ids'],
#                         "streamer": streamer,
#                         "max_new_tokens": 128,
#                         "temperature": 0.4
#                     })
#     thread.start()

#     for new_text in streamer:
#         if new_text.strip():
#             yield new_text
#     thread.join()

# def generate_response(input_text):
#     inputs = tokenizer(input_text, return_tensors="pt").to(device)
#     output_tokens = model.generate(
#         **inputs, 
#         max_new_tokens=256,
#         temperature=0.3,
#     )
    
#     output_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
#     return output_text

user_sessions = {}
search_params = {"metric_type": "L2", "params": {"ef": 30}}

def process_query(user_input, selected_file, system_id, batch_size=2):
    connections.connect("default", host="localhost", port="19530")
    try:
        # Initialize session if not already present
        if system_id not in user_sessions:
            user_sessions[system_id] = {
                'results': [],
                'current_index': 0,
                'last_query': None
            }
        session = user_sessions[system_id]

        # Handle "continue" command to fetch next batch of results
        if user_input.lower() == "continue":
            if not session['last_query']:
                yield "No previous query found. Please enter a new question."
                return
        
            if session['current_index'] > len(session['results']):
                yield "No more results to display."
                return
        else:
            # Generate the query vector for a new search
            session['last_query'] = user_input
            query_vector = embedding_model.encode([user_input]).tolist()

            # Perform search with optional file filtering
            if selected_file:
                formatted_files = ", ".join([f"'{file}'" for file in selected_file])
                expr = f"source in [{formatted_files}]"
            else:
                expr = None

            search_results = collection.search(
                data=query_vector,
                anns_field="vector", 
                param=search_params,
                limit=15,
                output_fields=["source", "page", "text"],
                consistency_level="Strong",
                expr=expr
            )
            # Convert SearchResult to a flat list of hits
            all_hits = []
            for hits in search_results:
                all_hits.extend(hits)  # Collect all individual hit objects
            session['results'] = all_hits
            session['current_index'] = 0

        # Fetch the current batch of results
        start_index = session['current_index']
        end_index = start_index + batch_size
        batch_results = session['results'][start_index:end_index]
        session['current_index'] = end_index
        # Process batch results into context for response
        context = '\n---\n'.join(
            f"File: {hit.entity.get('source')}\nPage: {hit.entity.get('page')}\nText: {hit.entity.get('text')}"
            for hit in batch_results
        )
        current_question = session['last_query'] if user_input.lower() == "continue" else user_input
        # Create the response prompt
        template = f"""
        You are an AI assistant designed to assist users by providing simple and clear answers to their questions.
        
        ### User Question:
        {current_question}
        
        Refer to the information below for support:
        ### Context:
        {context}

        INSTRUCTIONS:
            - your response should adhere one lead to the context without adding anything else
            - Make your response as cool
        """


        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        final_prompt = prompt.format(context=context, question=current_question)
        # for chunk in generate_streaming_response(final_prompt):
        #     yield chunk
        yield generate_response(final_prompt)
        sources = [
            f"Source: {hit.entity.get('source')} | Page: {hit.entity.get('page')}"
            for hit in batch_results
        ]
       
        yield '\n\n'.join(sources)

    except Exception as e:
        yield f"Error occurred: {str(e)}"

@lru_cache(maxsize=None)
def get_all_files_from_milvus():
    connections.connect("default",host = 'localhost', port='19530')
    collection = Collection(MILVUS_COLLECTION)
    iterator = collection.query_iterator(batch_size=1000,output_fields=["source"])
    results=[]
    while True:
        result = iterator.next()
        if not result:
            iterator.close()
            break
        results.extend(result)
    
    database_files = []
    for result in results:
        database_files.append(result['source'])
    database_files = list(set(database_files))
    connections.disconnect("default")
    return database_files

def get_all_folders_from_milvus():
    connections.connect("default", host="localhost", port="19530")
    collection = Collection(MILVUS_COLLECTION)
    collection.load()
    iterator = collection.query_iterator(batch_size=1000,output_fields=["source"])
    results=[]
    while True:
        result = iterator.next()
        if not result:
            iterator.close()
            break
        results.extend(result)
    database_locations = []
    for result in results:
        file_path = result['source']
        directory = os.path.dirname(file_path)
        database_locations.append(directory)
    database_locations = list(set(database_locations))
    connections.disconnect("default")
    return database_locations