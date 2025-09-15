FROM python:3.11-slim

WORKDIR /app

COPY requirements-heavy.txt .
RUN pip install torch==2.1.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements-heavy.txt

COPY requirements-light.txt .
RUN pip install -r requirements-light.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
