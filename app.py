import os
import json
import time
import random
from uuid import uuid4
from io import BytesIO
from fastapi import FastAPI, HTTPException
from pypdf import PdfReader
from canopy.knowledge_base import KnowledgeBase
from canopy.knowledge_base.record_encoder import OpenAIRecordEncoder
from canopy.models.data_models import Document, Query
from canopy.context_engine import ContextEngine
from canopy.models.data_models import UserMessage
from models import Message, Dataset
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
TO DO
 - Maybe have a logging function that outputs to a txt file? that uploads to s3
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
            detail=f"The document with the provided metadata already exists"
        )

    #Reads a PDF from S3 and extracts the text
    pdf_obj = s3_client.get_object(Bucket=env.get("LOADING_BUCKET"), Key=file_name)
    reader = PdfReader(BytesIO(pdf_obj["Body"].read()))
    pdf_content = ""
    for page in reader.pages:
        pdf_content += page.extract_text()
    file_stem = file_name.split(".")[0]

    #Writes the text to a file in the Docker image
    docker_file = open(f"docker_loaded_data/{file_stem}.txt", "w")
    docker_file.write(pdf_content)
    docker_file.close()

    #Opens the text file, upserts it, then removes it from the Docker image
    id = str(uuid4())
    with open(f'docker_loaded_data/{file_stem}.txt', 'r') as file:
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
    os.remove(f'docker_loaded_data/{file_stem}.txt')

    # Checks if the file has been uploaded with backoff
    retry_delay = 1  # Initial delay in seconds
    for _ in range(5):
        result = index.fetch([f"{id}_0"])
        if not result['vectors']:
            time.sleep(retry_delay)
            retry_delay *= 2  # Double the delay for the next attempt
            retry_delay += random.uniform(0, 1)  # Add jitter
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
    content = response.choices[0].message.content
    context_values = set()
    context = []
    for query in response.context['content']:
        for snippet in query['snippets']:
            values = (
                snippet['source'],
                snippet['metadata']['document_origin'],
                snippet['metadata']['primary_category'],
                snippet['metadata']['title']
            )
            if values in context_values:
                continue
            context_values.add(values)
            values_list = list(values)
            context_item = {}
            context_item['source'] = values_list.pop(0)
            context_item['document_origin'] = values_list.pop(0)
            context_item['primary_category'] = values_list.pop(0)
            context_item['title'] = values_list.pop(0)
            context.append(context_item)

    return {"response": content, "context": context}

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/test")
def test():
    encoder = OpenAIRecordEncoder(model_name=env.get("EMBEDDING_MODEL"))
    kb = KnowledgeBase(
        index_name=env.get("INDEX_NAME"),
        record_encoder=encoder
    )
    kb.connect()
    kb.verify_index_connection()
    results = kb.query([Query(text="Who are the Uyghurs?")])
    # results = kb.query([Query(text="uyghur", top_k=1, metadata_filter={"document_id": "fd5e0fcb-72bb-43ee-bf1d-44b389f632c4"})])
    # print(results)
    # index = pc.Index(env.get("INDEX_NAME"))
    # query = {"document_id":"fd5e0fcb-72bb-43ee-bf1d-44b389f632c4"}
    # results = index.query(
    #     id="fd5e0fcb-72bb-43ee-bf1d-44b389f632c4",
    #     # filter=query,
    #     top_k=1,
    #     include_metadata=True,
    # )
    print(results)
    # CAN DO: index.fetch(["UUIDHERE_0"]) much faster, index with ['vectors']
    # context_engine = ContextEngine(knowledge_base=kb)
    # # print(message)
    # results = context_engine.query([Query(text="Who are the Uyghurs?")], max_context_tokens=2867)
    # print(json.dumps(json.loads(results.to_text()), indent=2, ensure_ascii=False))
    # print(f"\n# tokens in context returned: {results.num_tokens}")
    print("completed kb test")
    return {"results": results}

@app.get("/test2")
def test2():
    encoder = OpenAIRecordEncoder(model_name=env.get("EMBEDDING_MODEL"))
    kb = KnowledgeBase(
        index_name=env.get("INDEX_NAME"),
        record_encoder=encoder
    )
    kb.connect()
    kb.verify_index_connection()
    # results = kb.query([Query(text="Who are the Uyghurs?")])
    # CAN DO: index.fetch(["UUIDHERE_0"]) much faster, index with ['vectors']
    context_engine = ContextEngine(knowledge_base=kb)
    results = context_engine.query([Query(text="Who are the Uyghurs?")], max_context_tokens=2867)
    # print(json.dumps(json.loads(results.to_text()), indent=2, ensure_ascii=False))
    # print(f"\n# tokens in context returned: {results.num_tokens}")
    print("completed kb test")
    return {"results": results}

@app.get("/test3")
def test3():
    s3_client