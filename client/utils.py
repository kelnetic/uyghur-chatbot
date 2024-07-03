import calendar
import time
from datetime import date

def format_context_doc(doc):
    doc_origin = f"**Origin**: [{doc['document_origin']}]({doc['source']})"
    doc_category = f"**Category**: {doc['primary_category']}"
    pub_date = None
    if doc.get('publication_day'):
        pub_date = date(
            doc['publication_year'], doc['publication_month'], doc['publication_day']
        )
        pub_date = f"**Date**: {pub_date.strftime('%B %-d, %Y')}"
    else:
        pub_date = f"**Date**: {calendar.month_name[doc['publication_month']]} {doc['publication_year']}"
    formatted_doc = f'''
    {doc_origin}  
    {doc_category}  
    {pub_date}
    '''
    return formatted_doc

def get_chat_inputs():
    return [
        "Ask me about Uyghurs",
        "Ask me about Uyghur forced labor",
        "Ask me about Uyghur forced imprisonment",
        "Ask me about Uyghur forced surveillance",
        "Ask me about Uyghur cultural erasure",
        "Ask me about the Uyghur diaspora",
        "Ask me about Uyghur transnational repression",
        "Ask me about the Uyghur genocide"
    ]

def get_response_iterable(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)