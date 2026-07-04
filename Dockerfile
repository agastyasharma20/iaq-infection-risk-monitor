# Dockerfile -- API service
# Builds a container for the FastAPI prediction service (api/main.py).
# The Streamlit dashboard has its own Dockerfile (see dashboard.Dockerfile)
# since it's a separate deployable process.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Model files must exist before running this container:
# run the training pipeline locally first, or add a training step here
# if you want the container to train on startup.

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
