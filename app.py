from fastapi import FastAPI
from pypdf import PdfReader

app = FastAPI()

"""
TO DO
 - If extension is PDF, need to just extract the text from it
 - If there is a file, remove it and replace it 
 - Extract it to data_text folder
 - Then create the endpoint for upload docs
 - Then go through the canopy set up
 - Install the canopy-sdk
"""

@app.get("/pdf_preview")
def pdf_preview():
    reader = PdfReader("data/IF10281.pdf")
    page = reader.pages[0]
    text = page.extract_text()
    print(text)
    return {"first page": text}

@app.get("/")
def root():
    return {"message": "Hello World"}