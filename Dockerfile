FROM python:3.10

RUN apt-get update && apt-get install -y \
    mesa-utils \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN pip install Cmake

RUN pip install face_recognition

COPY . .

CMD gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000