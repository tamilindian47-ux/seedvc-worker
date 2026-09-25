FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git libsndfile1 build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone Seed-VC source
RUN git clone --depth 1 https://github.com/Plachtaa/seed-vc.git /app/seed-vc

WORKDIR /app/seed-vc
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir runpod

WORKDIR /app
COPY src/handler.py /app/handler.py
COPY handler.py /app/src/handler.py

CMD ["python", "-u", "/app/handler.py"]
