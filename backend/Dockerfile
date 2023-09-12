FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -U pip &&\
    pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0:8000"]
