FROM python:3.11

COPY . .

WORKDIR /

RUN mkdir /docker_loaded_data
RUN --mount=type=cache,target=/root/.cache \
    pip install --no-cache-dir --upgrade -r /requirements.txt

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]