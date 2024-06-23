import os
import yaml
from canopy.tokenizer import Tokenizer
from canopy.tokenizer.openai import OpenAITokenizer
from canopy.knowledge_base import KnowledgeBase
from canopy.knowledge_base.record_encoder import OpenAIRecordEncoder
from canopy.context_engine import ContextEngine
from canopy.chat_engine import ChatEngine
from canopy.chat_engine.history_pruner import RecentHistoryPruner
from pinecone.grpc import PineconeGRPC as Pinecone

env = os.environ
Tokenizer.initialize(tokenizer_class=OpenAITokenizer, model_name="gpt-3.5-turbo")

def get_system_prompt():
    with open("canopy_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config["system_prompt"]

def get_encoder():
    return OpenAIRecordEncoder(model_name=env.get("EMBEDDING_MODEL"))

def get_kb():
    kb = KnowledgeBase(
        index_name=env.get("INDEX_NAME"),
        record_encoder=get_encoder()
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