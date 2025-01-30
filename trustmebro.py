def read_and_split_text(text_by_page, min_chunk_size=800, max_chunk_size=1200):
    """ Split text into chunks, respecting page boundaries """
    chunks = []


    def smart_chunk_processing(text, page_number):
        sentences = max([re.split(r'(?<=[!?])\s+', text), re.split(r'\n', text)], key=len)
        current_chunk = ""
        processed_chunks = []

        for sentence in sentences:
            if len(sentence)>max_chunk_size:
                while sentence:
                    chunk=sentence[:max_chunk_size]
                    processed_chunks.append(chunk)
                    sentence=sentence[max_chunk_size:]
                current_chunk=" "
                continue


            potential_chunk = (current_chunk +" "+ sentence).strip()

            if len(potential_chunk) > max_chunk_size:
                if len(current_chunk) >= min_chunk_size:
                    processed_chunks.append(current_chunk)
                    current_chunk=sentence
                else:
                    current_chunk=potential_chunk[:max_chunk_size]


            elif len(potential_chunk)>= min_chunk_size:
                current_chunk = potential_chunk
            else:
                current_chunk = potential_chunk


        if current_chunk and len(current_chunk) >- min_chunk_size:
            processed_chunks.append(current_chunk)


        return[(chunk, page_number)for chunk in processed_chunks]


    for page_num, page_text in text_by_page:
        page_chunks= smart_chunk_processing(page_text, page_num)
        chunks.extend(page_chunks)


    return chunks
