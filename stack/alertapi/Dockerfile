FROM python:3.8-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir Flask requests

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release && \
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5001
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]