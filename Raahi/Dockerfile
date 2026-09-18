FROM python:3.14-slim

WORKDIR /Raahi

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 Raahi_dev

RUN pip install --no-cache-dir -r requirements.txt

# Create staticfiles directory and set proper ownership before USER switch
RUN mkdir -p /Raahi/staticfiles && chown -R Raahi_dev:Raahi_dev /Raahi

USER Raahi_dev

COPY . .

EXPOSE 8000

CMD ["/entrypoint.sh"]
