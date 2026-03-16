FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for Postgres and C-extensions
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Important: Tell Python where to find your 'tracker' package
ENV PYTHONPATH=/app/src

# Run the app
CMD ["python", "src/tracker/main.py"]