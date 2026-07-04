# dashboard.Dockerfile -- Streamlit dashboard service
# Separate from the API's Dockerfile so the dashboard and API can be
# deployed and scaled independently (common practice, and required by
# most free-tier hosting platforms which expect one process per container).

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
