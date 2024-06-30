FROM python:3.11

WORKDIR /app

COPY ./server/requirements.txt /app/requirements_server.txt
COPY ./client/requirements.txt /app/requirements_client.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements_server.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements_client.txt

COPY . /app
RUN chmod +x docker-entrypoint.sh

EXPOSE 8501

# Expose ports
EXPOSE 80 8501 7860

ENV PYTHONPATH "${PYTHONPATH}:/app/server"

RUN mkdir -p /var/cache/nginx \
    /var/log/nginx \
    /var/lib/nginx
RUN touch /var/run/nginx.pid

RUN useradd -m -u 1000 user

RUN chown -R user:user /var/cache/nginx \
    /var/log/nginx \
    /var/lib/nginx \
    /var/run/nginx.pid

# Run entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]