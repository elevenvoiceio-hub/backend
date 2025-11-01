# Stage 1: Build Stage
FROM python:3.11-slim AS builder

# Set the working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies in a virtual environment for better isolation
RUN python -m venv /venv
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Stage 2: Production Stage (Final, minimal image)
FROM gcr.io/distroless/python3-slim

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /venv /venv
COPY --from=builder /app /app

# Cloud Run injects the PORT environment variable.
# Ensure your app listens on $PORT (default is 8080).
ENV PORT 8080

# Use the virtual environment Python interpreter
ENV PATH="/venv/bin:$PATH"

# Run the application using Gunicorn or a similar WSGI server
# NOTE: Replace "main:app" with the correct entry point for your framework (e.g., app.wsgi_app for Django)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]