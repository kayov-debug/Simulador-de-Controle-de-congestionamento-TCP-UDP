FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_server.py", "--protocol", "udp", "--host", "0.0.0.0", "--port", "9000", "--duration", "10", "--rate-limit", "200"]