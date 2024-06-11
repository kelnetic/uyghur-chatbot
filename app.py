import os
from uuid import uuid4
from fastapi import FastAPI
from pypdf import PdfReader
from canopy.tokenizer import Tokenizer
from canopy.tokenizer.cohere import CohereAPITokenizer
from canopy.knowledge_base import KnowledgeBase
from canopy.knowledge_base.record_encoder.cohere import CohereRecordEncoder
from canopy.models.data_models import Document, Query

env = os.environ
app = FastAPI()
Tokenizer.initialize(tokenizer_class=CohereAPITokenizer, model_name="embed-multilingual-v3.0")

"""
TO DO
 - If extension is PDF, need to just extract the text from it
 - If there is a file, remove it and replace it 
 - Extract it to data_text folder
 - Then create the endpoint for upload docs
 - Then go through the canopy set up
 - Install the canopy-sdk
 - Could have a list of ingest files in a text file, then compare that with any new file. Continue it if already ingested
"""

@app.get("/pdf_preview")
def pdf_preview():
    file_name = "IF10281"
    reader = PdfReader("data/IF10281.pdf")
    pdf_content = ""
    for page in reader.pages:
        pdf_content += page.extract_text()

    docker_file = open(f"docker_loaded_data/{file_name}.txt", "w")
    docker_file.write(pdf_content)
    docker_file.close()
    
    # Writing the file to the host if verification is needed
    host_file = open(f"data_text/{file_name}.txt", "w")
    host_file.write(pdf_content)
    host_file.close()

    tokenizer = Tokenizer()
    print(tokenizer.tokenize("Hello world!"))
    encoder = CohereRecordEncoder(model_name=env.get("CO_KB_MODEL"))
    kb = KnowledgeBase(
        index_name=env.get("INDEX_NAME"),
        record_encoder=encoder
    )
    kb.connect()
    kb.verify_index_connection()

    with open(f'docker_loaded_data/{file_name}.txt', 'r') as file:
        documents = [Document(id=str(uuid4()),
                            text=file.read(),
                            source="https://crsreports.congress.gov/product/pdf/IF/IF10281",
                            metadata={
                                "title": "China Primer: Uyghurs",
                                "primary_category": "brief",
                                "doc_origin": "Congressional Research Service"
                            })]
        kb.upsert(documents)

    results = kb.query([Query(text="Uyghur ethnic people"),
                        Query(text="Uyghur ethnic people",
                            top_k=10)])

    print(results[0].documents[0].text)
    # output: Arctic Monkeys are an English rock band formed in Sheffield in 2002.

    print(f"score - {results[0].documents[0].score:.4f}")
    # output: score - 0.8942

    return {"PDF Content": pdf_content}

@app.get("/")
def root():
    return {"message": "Hello World"}