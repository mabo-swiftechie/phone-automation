FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY app/ app/

RUN pip install --no-cache-dir .

EXPOSE 8501 8000

ENV PHONE_AUTOMATION_DATA=/data

CMD ["phone-automation"]
