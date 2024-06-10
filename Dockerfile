FROM python:3.11

COPY . .

WORKDIR /

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--reload"]