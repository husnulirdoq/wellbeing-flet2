FROM python:3.12

# Install library esensial untuk Flet (Debian Version)
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["flet", "run", "--web", "--port", "8080"]