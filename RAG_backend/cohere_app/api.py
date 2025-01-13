from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from functools import lru_cache 
from pymilvus import connections, Collection
import os
from .globals import global_collection_name
from .models import CurrentUsingCollection

MODEL_NAME = "meta-llama/Llama-3.2-3B"
MILVUS_COLLECTION = 'ram_test'
device = "cuda"

# def get_current_using_collection_value():
#     try:
#         current_collection = CurrentUsingCollection.objects.first()  
#         if current_collection:
#             # Assign the collection name to a variable
#             collection_name = current_collection.current_using_collection
#             return str(collection_name)
#         else:
#             return None 
#     except Exception as e:
#         return str(e) 

# collection_name = get_current_using_collection_value()

# if collection_name:
#     MILVUS_COLLECTION = collection_name
#     print("MILVUS_COLLECTION:",MILVUS_COLLECTION)

def load_model_and_tokenizer():
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME,token='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').to(device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME,token = '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')
    return model, tokenizer

model, tokenizer = load_model_and_tokenizer()

connections.connect("default", host="localhost", port="19530")
collection = Collection(MILVUS_COLLECTION)
collection.load()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_streaming_response(input_text):
    # print("Received in stream",input_text)
    inputs = tokenizer(input_text, return_tensors="pt").to(device)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    thread = Thread(target=model.generate,
                    kwargs={
                        "input_ids": inputs['input_ids'],
                        "streamer": streamer,
                        "max_new_tokens": 512,
                        "do_sample": False,
                        "temperature": 0.5
                    })
    print("Starting the generation thread...")
    thread.start()

    for new_text in streamer:
        if new_text.strip():
            yield new_text
    thread.join()
    print("Thread has completed.")

user_sessions = {}
search_params = {"metric_type": "L2", "params": {"ef": 30}}

def process_query(user_input, selected_file, system_id, batch_size=5):
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
        template = """
        Use the provided context to generate a precise and accurate answer to the question below.
        Context:
        {context}

        Question:
        {question}

        Guidelines for Response:
           - Base the response on the provided context when applicable.
           - If the context does not address the question, state that explicitly and offer to help clarify or explore related next steps.
           - Avoid unnecessary elaboration, repetition, or irrelevant details.
           - Make the answers compact for user understanding.
        Answer:
        """
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        final_prompt = prompt.format(context=context, question=current_question)
        print(final_prompt)
        # Generate the response based on the prompt
        for chunk in generate_streaming_response(final_prompt):
            yield chunk

        # Yield the sources for the current batch
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
    print(database_files)
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