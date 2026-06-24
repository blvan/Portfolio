FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl cron tini util-linux && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir pandas pyarrow duckdb requests fsspec adlfs

# ставим crontab из файла
RUN crontab /app/docker/crontab

RUN mkdir -p /app/logs

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["bash","-lc","/usr/sbin/cron && touch /app/logs/.keep && tail -F /app/logs/*.log"]
