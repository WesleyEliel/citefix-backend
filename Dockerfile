FROM python:3.10-slim-buster as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERD 1

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

WORKDIR /cite-fix

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt && \
    apt purge -y --auto-remove build-essential && \
    chown -R app:app /cite-fix && \
    chmod 777 -R /cite-fix && \
    chmod +x server.sh
#    chown -R app:app /app && \
#    chmod +x server.sh


RUN pwd && ls



USER app

COPY . /cite-fix

EXPOSE 8000

#ENTRYPOINT ["supervisord", "-c", "supervisor.conf"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
