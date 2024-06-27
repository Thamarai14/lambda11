FROM deepaksd0/fastapi_gunicorn_uvicorn:python_3.10-slim-bullseye-multi
COPY . /app
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8490
WORKDIR /app
LABEL maintainer="Linga"

