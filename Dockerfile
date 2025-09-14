# Python 3.11 resmi imajını kullan
FROM python:3.11-slim

WORKDIR /app

# Önce ağır bağımlılıkları yükle (cache edilir, nadiren değişir)
COPY requirements-heavy.txt .
RUN pip install torch==2.1.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements-heavy.txt

# Sonra hafif bağımlılıkları yükle (sık değişebilir)
COPY requirements-light.txt .
RUN pip install -r requirements-light.txt

# Uygulama dosyalarını kopyala
COPY . .

EXPOSE 8000

# Uvicorn ile FastAPI başlat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
