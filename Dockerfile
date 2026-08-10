FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd --create-home --uid 10001 appuser
USER 10001

EXPOSE 8080

CMD ["python", "app.py"]
