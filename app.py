import os
import json
from pydantic import BaseModel
from uuid import uuid4
from fastapi import FastAPI
from pypdf import PdfReader
from canopy.tokenizer import Tokenizer
from canopy.tokenizer.openai import OpenAITokenizer
from canopy.knowledge_base import KnowledgeBase
from canopy.knowledge_base.record_encoder import OpenAIRecordEncoder
from canopy.models.data_models import Document, Query
from canopy.context_engine import ContextEngine
from canopy.chat_engine import ChatEngine
from canopy.models.data_models import UserMessage
from canopy.chat_engine.history_pruner import RecentHistoryPruner

env = os.environ
app = FastAPI()
Tokenizer.initialize(tokenizer_class=OpenAITokenizer, model_name="gpt-3.5-turbo")

encoder = OpenAIRecordEncoder(model_name=env.get("EMBEDDING_MODEL"))
kb = KnowledgeBase(
    index_name=env.get("INDEX_NAME"),
    record_encoder=encoder
)
kb.connect()
kb.verify_index_connection()
context_engine = ContextEngine(knowledge_base=kb)
chat_engine = ChatEngine(context_engine=context_engine, history_pruner=RecentHistoryPruner(min_history_messages=1))

class Message(BaseModel):
    content: str

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

@app.get("/ingest_documents")
def ingest_documents():
    #Can make it a post request with file path and metadata
    file_name = "22-08-31-final-assesment"
    reader = PdfReader("data/22-08-31-final-assesment.pdf")
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

    with open(f'docker_loaded_data/{file_name}.txt', 'r') as file:
        documents = [Document(id=str(uuid4()),
                            text=file.read(),
                            source="https://www.ohchr.org/sites/default/files/documents/countries/2022-08-31/22-08-31-final-assesment.pdf",
                            metadata={
                                "title": "OHCHR Assessment of human rights concerns in the Xinjiang Uyghur Autonomous Region, People's Republic of China",
                                "primary_category": "report",
                                "document_origin": "Office of the United Nations High Commissioner for Human Rights"
                            })]
        kb.upsert(documents)

    return {"200 OK"}

@app.post("/chat")
def chat(message: Message):
    response = chat_engine.chat(messages=[UserMessage(content=message.content)], stream=False)
    content = response.choices[0].message.content
    return {
        "Query": message.content,
        "Chat response": content
        }

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
    context_engine = ContextEngine(knowledge_base=kb)
    # print(message)
    results = context_engine.query([Query(text="Who are the Uyghurs?")], max_context_tokens=2867)
    print(json.dumps(json.loads(results.to_text()), indent=2, ensure_ascii=False))
    print(f"\n# tokens in context returned: {results.num_tokens}")
    return {"results": results}