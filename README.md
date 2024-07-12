# uyghur-chatbot

This is meant to be a RAG enabled chatbot that will provide users with information concerning the current Uyghur persecution. 
The current plans are to:
- ✅ Upload files, and extract text from them
- ✅ Use Pinecone's Canopy framework to handle embedding, retrieval, and chatting
- ✅ Use Streamlit to build a simple frontend view
- ✅ Host on Streamlit cloud
- 🔜 Will need to finetune the retrieval and chatting so that the chatbot produces detailed results, makes users ask more questions, and can carry a conversation

If you are interested in viewing the forked Canopy repo I have added changes to [please check out this link.](https://github.com/kelnetic/canopy)

## How to run the server locally:
- Run `docker compose up --build`. The build configurations are contained in the Docker compose file.

## Canopy tips:
If you want to view results from the knowledge base you can do the following:
```
results = kb.query([Query(text="uyghur", top_k=1, metadata_filter={"document_id": "fd5e0fcb-72bb-43ee-bf1d-44b389f632c4"})])
print(results)
```
If you want to view results from the context engine you can do the following:
```
context_engine = ContextEngine(knowledge_base=kb)
results = context_engine.query([Query(text="Who are the Uyghurs?")], max_context_tokens=2867)
print(json.dumps(json.loads(results.to_text()), indent=2, ensure_ascii=False))
print(f"\n# tokens in context returned: {results.num_tokens}")
```

## Streamlit tips:
To print to the console you can do:
```
os.write(1,f"{CODE}\n".encode()) 
```
