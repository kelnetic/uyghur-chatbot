import os

# Get the list of all files and directories
path = "/etc"
dir_list = os.listdir(path)
print("Files and directories in '", path, "' :")
# prints all files
print(dir_list)

# Get the list of all files and directories
path = "/"
dir_list = os.listdir(path)
print("Files and directories in '", path, "' :")
# prints all files
print(dir_list)

APP_ROOT = os.path.join(os.path.dirname(__file__))
print("Files and directories in '", APP_ROOT, "' :")
# prints all files
print(dir_list)


import time
import random
from uuid import uuid4
from io import BytesIO
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Depends,
    Request
)
from canopy.models.data_models import Document, UserMessage
from models import Message, Dataset
from pypdf import PdfReader
from utils import AppManager, check_app_mode

load_dotenv("/etc/secrets/.env")
env = os.environ
app = FastAPI()
#UyghurChatbot Core
uc_core = AppManager()

"""
TODO
 - Maybe have a logging function that outputs to a txt file? that uploads to s3
 - Guarantee that the chatbot will confirm the existence of a chatbot as well as East Turkestan, whenever Xinjiang is mentioned
 - But we could hardcode East Turkestan to always appear before Xinjiang
"""

@app.post("/ingest", dependencies=[Depends(check_app_mode)])
def ingest_documents(dataset: Dataset):
    file_name = dataset.file_name
    #Make a query to see if the document already exists in the vector DB, can be re-used when upserted
    query = {
        "file_name": file_name,
        "source": dataset.source_link,
        "title": dataset.title,
        "primary_category": dataset.primary_category,
        "document_origin": dataset.document_origin,
        "publication_year": dataset.publication_year,
        "publication_month": dataset.publication_month,
    }
    #Some sources may not have a publication day
    if dataset.publication_day:
        query["publication_day"] = dataset.publication_day

    results = uc_core.index.query(
        vector=[0] * 1536,
        filter=query,
        top_k=1
    )
    if results["matches"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The document with the provided metadata already exists"
        )

    #Reads a PDF from S3 and extracts the text
    try:
        pdf_obj = uc_core.s3_client.get_object(Bucket=env.get("LOADING_BUCKET"), Key=file_name)
        reader = PdfReader(BytesIO(pdf_obj["Body"].read()))
        pdf_content = ""
        for page in reader.pages:
            pdf_content += page.extract_text()

        #Upserts the content that was extracted
        id = str(uuid4())
        documents = [Document(
            id=id,
            text=pdf_content,
            source=query.pop("source"),
            metadata=query
            )]
        uc_core.kb.upsert(documents)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error with extracting or upserting text: {error}"
        )

    # Checks if the file has been uploaded with backoff
    retry_delay = 1
    for _ in range(5):
        result = uc_core.index.fetch([f"{id}_0"])
        if not result['vectors']:
            time.sleep(retry_delay)
            retry_delay *= 2
            retry_delay += random.uniform(0, 1)
        # Upon successful upsert, "move" the file to the uploaded bucket
        else:
            copy_source = {'Bucket': env.get("LOADING_BUCKET"), 'Key': file_name}
            uc_core.s3_client.copy(copy_source, env.get("UPLOADED_BUCKET"), file_name)
            uc_core.s3_client.delete_object(Bucket=env.get("LOADING_BUCKET"), Key=file_name)
            return {f"The document with id {id} was successfully upserted"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"The document with id {id} was upserted but not fetched, please verify on Pinecone"
    )

@app.post("/chat")
def chat(message: Message, request: Request):
    # if request.headers.origin != 'https://uyghur-chatbot.streamlit.app/':
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="This operation is forbidden"
    #     )
    response = uc_core.chat_engine.chat(messages=[UserMessage(content=message.content)])
    #TODO: Check the response choices and see what message is the best, should it be the longest message? The one with the most statistics? Mentions of genocide?
    #Can create a custom instance of query generator with a defualt system prompt that might be able to add more queries
    #I think in the query generator, can include a sentence to not send a function if it asking what the purpose of the chatbot is, or who "you" are
    print(f"Printing request headers: {request.headers}")
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
                "publication_year": int(snippet['metadata']['publication_year']),
                "publication_month": int(snippet['metadata']['publication_month']),
            }
            if snippet['metadata'].get('publication_day'):
                context_item["publication_day"] = int(snippet['metadata']['publication_day'])

            context_values_tuple = tuple(context_item.values())
            if context_values_tuple not in context_values:
                context_values.add(context_values_tuple)
                context.append(context_item)

    return {"response": content, "context": context}