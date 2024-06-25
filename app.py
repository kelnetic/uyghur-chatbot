import os
import time
import random
from uuid import uuid4
from io import BytesIO
from fastapi import FastAPI, HTTPException
from canopy.models.data_models import Document, UserMessage
from models import Message, Dataset
from pypdf import PdfReader
from dependencies import (
    get_system_prompt,
    get_kb,
    get_context_engine,
    get_chat_engine,
    get_index,
    get_s3_client
)

env = os.environ
app = FastAPI()
system_prompt = get_system_prompt()
kb = get_kb()
#For retrieving context in a separate endpoint
context_engine = get_context_engine(kb=kb)
chat_engine = get_chat_engine(context_engine=context_engine)
index = get_index()
s3_client = get_s3_client()

"""
TODO
 - Maybe have a logging function that outputs to a txt file? that uploads to s3
 - Guarantee that the chatbot will confirm the existence of a chatbot as well as East Turkestan, whenever Xinjiang is mentioned
 - But we could hardcode East Turkestan to always appear before Xinjiang
"""

@app.post("/ingest")
def ingest_documents(dataset: Dataset):
    file_name = dataset.file_name
    source_link = dataset.source_link
    title = dataset.title
    category = dataset.primary_category
    origin = dataset.document_origin
    publication_date = str(dataset.publication_date) if dataset.publication_date is not None else ""

    #Make a query to see if the document already exists in the vector DB
    query = {
        "source": source_link,
        "title": title,
        "primary_category": category,
        "document_origin": origin,
        "publication_date": publication_date
    }
    results = index.query(
        vector=[0] * 1536,
        filter=query,
        top_k=1
    )
    if results["matches"]:
        raise HTTPException(
            status_code=400,
            detail="The document with the provided metadata already exists"
        )

    #Reads a PDF from S3 and extracts the text
    pdf_obj = s3_client.get_object(Bucket=env.get("LOADING_BUCKET"), Key=file_name)
    reader = PdfReader(BytesIO(pdf_obj["Body"].read()))
    pdf_content = ""
    for page in reader.pages:
        pdf_content += page.extract_text()
    file_stem = file_name.split(".")[0]

    #Writes the text to a file in the Docker image
    docker_file = open(f"tmp/docker_loaded_data/{file_stem}.txt", "w")
    docker_file.write(pdf_content)
    docker_file.close()

    #Opens the text file, upserts it, then removes it from the Docker image
    id = str(uuid4())
    with open(f'tmp/docker_loaded_data/{file_stem}.txt', 'r') as file:
        documents = [Document(id=id,
                        text=file.read(),
                        source=source_link,
                        metadata={
                            "title": title,
                            "primary_category": category,
                            "document_origin": origin,
                            "file_name": file_name,
                            "publication_date": publication_date
                        })]
        kb.upsert(documents)
    os.remove(f'tmp/docker_loaded_data/{file_stem}.txt')

    # Checks if the file has been uploaded with backoff
    retry_delay = 1
    for _ in range(5):
        result = index.fetch([f"{id}_0"])
        if not result['vectors']:
            time.sleep(retry_delay)
            retry_delay *= 2
            retry_delay += random.uniform(0, 1)
        # Upon successful upsert, "move" the file to the uploaded bucket
        else:
            copy_source = {'Bucket': env.get("LOADING_BUCKET"), 'Key': file_name}
            s3_client.copy(copy_source, env.get("UPLOADED_BUCKET"), file_name)
            s3_client.delete_object(Bucket=env.get("LOADING_BUCKET"), Key=file_name)
            return {f"The document with id {id} was successfully upserted"}

    raise HTTPException(
        status_code=404,
        detail=f"The document with id {id} was upserted but not fetched, please verify on Pinecone"
    )

@app.post("/chat")
def chat(message: Message):
    response = chat_engine.chat(messages=[UserMessage(content=message.content)], stream=False)
    #TODO: Check the response choices and see what message is the best, should it be the longest message? The one with the most statistics? Mentions of genocide?
    content = response.choices[0].message.content
    context_values = set()
    context = []
    # Iterates through context snippets and only adds unique sources to the context
    for query in response.context['content']:
        for snippet in query['snippets']:
            context_item = {
                "source": snippet['source'],
                "title": snippet['metadata']['title'],
                "document_origin": snippet['metadata']['document_origin'],
                "primary_category": snippet['metadata']['primary_category'],
                "publication_date": snippet['metadata']['publication_date']
            }
            if tuple(context_item.values()) not in context_values:
                context_values.add(tuple(context_item.values()))
                context.append(context_item)

    return {"response": content, "context": context}

@app.get("/")
def root():
    return {"message": "Hello World"}
