FROM python:3.11-slim

# System dependencies required by OpenCV and other native libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Remove the bundled model file — ultralytics downloads it at runtime
RUN rm -f yolov8m.pt yolov8s.pt yolov8n.pt

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
