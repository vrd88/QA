import re
from tqdm import tqdm
import fitz
from langchain_core.documents import Document
from pptx import Presentation
from docx import Document as DocxDocument
import openpyxl
import csv
from langchain_community.vectorstores import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
from .enable_logging import logger 
from cohere_app.Chunking_UI import db_utility
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': "cuda"})
model = ocr_predictor(pretrained=True)
model = model.to('cuda')
OCR_LIST = []

def extract_text_pdf(pdf_path):
    text_by_page = []
    try:
        pdf = fitz.open(pdf_path)
    except Exception as e:
        return [], "Can't open the file ERROR"
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text()
        # we need to clean the text here.
        if not text:
            OCR_LIST.append(pdf_path)
            return [], "OCR required - ERROR"
        else:
            text_by_page.append((page_num, text))
    return text_by_page, "Text extraction done"

def process_ocr_document(pdf_path):
    """ Extract text using OCR from each page of the PDF """
    try:
        """ Extract text using OCR from each page of the PDF """
        text_by_page = []
        doc = DocumentFile.from_pdf(pdf_path)
        result = model(doc)
        for page_num, page in enumerate(result.pages, start=1):
            page_text = ""
            words = []
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        words.append(word)
            sorted_words = sorted(words, key=lambda word: (word.geometry[0][1], word.geometry[0][0]))
            page_text = " ".join([word.value for word in sorted_words])
            text_by_page.append((page_num, page_text))
        return text_by_page, "text extraction done"
    except Exception as e:
        logger.error(f"Error extracting OCR text from {pdf_path}: {e}")
        return [], f"OCR FILE ERROR : {e}"


def process_pptx(file_path):
    """ Process .pptx file and extract text slide by slide """
    try:
        prs = Presentation(file_path)
        text_by_slide = []
        for i, slide in enumerate(prs.slides):
            slide_text = "\n".join([shape.text for shape in slide.shapes if hasattr(shape, "text")])
            text_by_slide.append((i + 1, slide_text))
        return text_by_slide, "text extraction done" 
    except Exception as e:
        logger.exception(f"Error processing PPTX file {file_path}")
        return [], f"PPTX FILE ERROR : {e}"


def process_docx(file_path):
    """ Process .docx file and extract text """
    try:
        doc = DocxDocument(file_path)
        text_by_paragraph = [(i + 1, para.text) for i, para in enumerate(doc.paragraphs)]
        return text_by_paragraph, "text extraction done" 
    except Exception as e:
        logger.exception(f"Error processing DOCX file {file_path}")
        return [], f"DOCX FILE ERROR : {e}"


def process_txt(file_path):
    """ Process .txt file and extract text """
    try:
        with open(file_path, 'r') as f:
            text = f.read()
        return [(1, text)], "text extraction done"  # Text file considered as one page
    except Exception as e:
        logger.error(f"Error processing TXT file {file_path}: {e}")
        return [], f"TEXT FILE ERROR : {e}"


def process_xlsx(file_path):
    """ Process .xlsx file and extract text sheet by sheet """
    try:
        workbook = openpyxl.load_workbook(file_path)
        text_by_sheet = []
        for sheet in workbook.sheetnames:
            worksheet = workbook[sheet]
            sheet_text = "\n".join([",".join([str(cell.value) for cell in row]) for row in worksheet.iter_rows()])
            text_by_sheet.append((sheet, sheet_text))
        return text_by_sheet, "text extraction done"
    except Exception as e:
        logger.exception(f"Error processing XLSX file {file_path}")
        return [], f"EXCEL FILE ERROR : {e}"


def process_csv(file_path):
    """ Process .csv file and extract text """
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            text = "\n".join([",".join(row) for row in reader])
        return [(1, text)], "text extraction done"  # Consider CSV as one page
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {e}")
        return [()],  f"CSV FILE ERROR : {e}"


def clean_text(text):
    """ Clean the extracted text by removing unwanted characters and formatting """
    text = re.sub(r'\.{3,}', '.', text)
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if len(line.split()) >= 4]
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'^\s*$', '', cleaned_text, flags=re.MULTILINE)
    return cleaned_text.strip()


def read_and_split_text(text_by_page, min_chunk_size=800, max_chunk_size=1200):
    """ Advanced text chunking with intelligent merging and splitting """
    chunks = []

    def smart_chunk_processing(text, page_number):
        sentences = max([re.split(r'(?<=[.!?])\s+', text), re.split(r'\n', text)], key=len)
        current_chunk = ""
        processed_chunks = []

        for sentence in sentences:
            if len(sentence) > max_chunk_size:
                while sentence:
                    chunk = sentence[:max_chunk_size]
                    processed_chunks.append(chunk)
                    sentence = sentence[max_chunk_size:]
                current_chunk = ""
                continue

            potential_chunk = (current_chunk + " " + sentence).strip()
            
            if len(potential_chunk) > max_chunk_size:
                if len(current_chunk) >= min_chunk_size:
                    processed_chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    current_chunk = potential_chunk[:max_chunk_size]
            
            elif len(potential_chunk) >= min_chunk_size:
                current_chunk = potential_chunk
            
            else:
                current_chunk = potential_chunk

        if current_chunk and len(current_chunk) >= min_chunk_size:
            processed_chunks.append(current_chunk)
        
        return [(chunk, page_number) for chunk in processed_chunks]


    for page_num, page_text in text_by_page:
        page_chunks = smart_chunk_processing(page_text, page_num)
        chunks.extend(page_chunks)

    return chunks


def process_document(file_path):
    """ Process a single document """
    try:
        text_by_page = []
        message = ""
        if file_path.endswith('.pdf') or file_path.endswith('.PDF'):
            text_by_page, message = extract_text_pdf(file_path)
        elif file_path.endswith('.pptx'):
            text_by_page, message = process_pptx(file_path)
        elif file_path.endswith('.docx'):
            text_by_page, message = process_docx(file_path)
        elif file_path.endswith('.txt'):
            text_by_page, message = process_txt(file_path)
        elif file_path.endswith('.xlsx'):
            text_by_page, message = process_xlsx(file_path)
        elif file_path.endswith('.csv'):
            text_by_page, message = process_csv(file_path)
        return text_by_page, message
    #TODO - i dont think so this except requires to store the error files
    except Exception as e:
        return [], f"Error processing document {file_path}\n{e}"

def create_langchain_documents(found_files, collection_name):
    """
    Create langchain documents from the extracted and processed text.

    This function processes PDF, PPTX, DOCX, TXT, XLSX, and CSV files in parallel.
    If a PDF requires OCR processing (no text found), it's handled sequentially.
    """
    db_utility.create_user_access(collection_name)
    db_utility.chunking_monitor()
    db_utility.create_error_files(collection_name)

    # Process found files
    for file_index, file in enumerate(found_files):
        text_by_page, message = process_document(file)
        if text_by_page and 'error' not in message.lower():
            chunks = read_and_split_text(text_by_page)
            logger.info(f"current processing file {file} with {len(str(chunks))}")
            if len(str(chunks)) > 5:
                for chunk, page_num in chunks:
                    documents = []
                    doc = Document(page_content=chunk, metadata={'source': file, 'page': str(page_num)})
                    documents.append(doc)

                    if documents:
                        Milvus.from_documents(documents, embeddings, collection_name=collection_name,
                                            connection_args={'uri': "http://localhost:19530"})
            
                    
                db_utility.insert_user_access(file, 'YES', message, collection_name)
            else:
                db_utility.store_error_files_with_error(collection_name, file, "Too small chunk size -- document skipped")
        elif "error" in message.lower() and "ocr" not in message.lower():
            db_utility.store_error_files_with_error(collection_name, file, message)
            logger.error(f"Error in the document - Skipping {file}")
        progress_percentage = (file_index + 1) / len(found_files) * 100
        yield {"progress_percentage": progress_percentage, "current_progress": file_index + 1, "total_files": len(found_files)}

    # Process OCR files
    documents = []
    for ocr_file_index, ocr_file in enumerate(tqdm(OCR_LIST, desc="Overall Progress")):
        tqdm().set_description(f"Processing File :  {ocr_file}")
        text_by_page, message = process_ocr_document(ocr_file)
        if text_by_page:
            chunks = read_and_split_text(text_by_page)
            logger.info(f"current processing file {file} with {len(str(chunks))}")
            if len(str(chunks)) > 5:
                for chunk, page_num in chunks:
                    documents = []
                    doc = Document(page_content=chunk, metadata={'source': ocr_file, 'page': str(page_num)})
                    documents.append(doc)
                    if documents:
                        Milvus.from_documents(documents, embeddings, collection_name=collection_name,
                                            connection_args={'uri': "http://localhost:19530"})
                db_utility.update_ocr_status(ocr_file, collection_name)
        progress_percentage = (ocr_file_index + 1) / len(OCR_LIST) * 100
        yield {"progress_percentage": progress_percentage, "current_progress": ocr_file_index + 1, "total_files": len(OCR_LIST)}
