FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy everything from your local / folder into the container's /app directory
COPY app.py /app/
COPY lib/ /app/lib/
COPY prompts/ /app/prompts/
COPY api/ /app/api/
COPY requirements.txt /app/

# Install dependencies from requirements.txt now available in /app
RUN pip install -r requirements.txt


# Start FastAPI using Uvicorn on port 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
