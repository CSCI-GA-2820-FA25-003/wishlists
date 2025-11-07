FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --no-cache-dir --upgrade pip pipenv && \
    PIPENV_VENV_IN_PROJECT=1 pipenv install --system --deploy --ignore-pipfile

# Copy application code
COPY . /app

# Start Flask with gunicorn
RUN python -m pip install --no-cache-dir gunicorn
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "wsgi:app"]
