import os
import yaml
import boto3
from fastapi import HTTPException, status
from canopy.tokenizer import Tokenizer
from canopy.tokenizer.openai import OpenAITokenizer
from canopy.knowledge_base import KnowledgeBase
from canopy.knowledge_base.reranker import CohereReranker
from canopy.knowledge_base.record_encoder import OpenAIRecordEncoder
from canopy.context_engine import ContextEngine
from canopy.chat_engine import ChatEngine
from canopy.chat_engine.history_pruner import RecentHistoryPruner
from pinecone.grpc import PineconeGRPC as Pinecone

env = os.environ
Tokenizer.initialize(tokenizer_class=OpenAITokenizer, model_name="gpt-3.5-turbo")

class AppManager:
    def __init__(self):
        self.kb = get_kb()
        self.context_engine = get_context_engine(kb=self.kb)
        self.chat_engine = get_chat_engine(context_engine=self.context_engine)
        self.index = get_index()
        self.s3_client = get_s3_client()

def get_system_prompt():
    with open(env.get("CANOPY_CONFIG_FILE"), "r") as f:
        config = yaml.safe_load(f)
    return config["system_prompt"]

def get_encoder():
    return OpenAIRecordEncoder(model_name=env.get("EMBEDDING_MODEL"))

def get_cohere_reranker():
    return CohereReranker(
        model_name = env.get("RERANKING_MODEL"),
        n_results = 5,
        api_key = env.get("CO_API_KEY")
    )

def get_kb():
    kb = KnowledgeBase(
        index_name=env.get("INDEX_NAME"),
        record_encoder=get_encoder(),
        default_top_k=int(env.get("DEFAULT_TOP_K")),
        reranker=get_cohere_reranker()
    )
    kb.connect()
    kb.verify_index_connection()
    return kb

def get_context_engine(kb=get_kb()):
    return ContextEngine(knowledge_base=kb)

def get_chat_engine(context_engine=get_context_engine()):
    chat_engine = ChatEngine(
        context_engine=context_engine,
        history_pruner=RecentHistoryPruner(min_history_messages=1),
        system_prompt=get_system_prompt()
    )
    return chat_engine

def get_index():
    pc = Pinecone(api_key=env.get("PINECONE_API_KEY"))
    index = pc.Index(env.get("INDEX_NAME"))
    return index

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=env.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=env.get("AWS_SECRET_ACCESS_KEY"),
        region_name=env.get("AWS_REGION")
    )

def check_app_mode():
    if env.get("APP_MODE") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is forbidden"
        )