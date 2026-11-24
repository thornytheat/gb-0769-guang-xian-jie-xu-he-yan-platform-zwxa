FROM python:3.12-slim
WORKDIR /station
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FIBER_DB=/var/lib/fiber/inspection.sqlite PYTHONDONTWRITEBYTECODE=1
CMD ["python", "-m", "flask", "--app", "app.main", "run", "--host=0.0.0.0", "--port=8000"]
