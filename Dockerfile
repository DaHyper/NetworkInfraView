FROM python:3.11-slim

WORKDIR /app

# Install system deps (WeasyPrint needs cairo/pango)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p /data

ENV DATABASE_URL=sqlite:////data/networkinfraview.db
ENV HOST=0.0.0.0
ENV PORT=5050
ENV FLASK_DEBUG=false

EXPOSE 5050

CMD ["python", "run.py"]
