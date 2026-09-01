FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Pre-download ML models at build time (avoids cold start delay)
RUN python -c "
from transformers import pipeline
print('Downloading emotion model...')
pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')
print('Downloading zero-shot model...')
pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
print('Models ready')
"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
