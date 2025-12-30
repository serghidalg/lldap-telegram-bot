FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl iputils-ping jq && rm -rf /var/lib/apt/lists/*

# Install lldap-cli
RUN curl -L https://raw.githubusercontent.com/Zepmann/lldap-cli/refs/heads/main/lldap-cli -o /usr/local/bin/lldap-cli \
    && chmod +x /usr/local/bin/lldap-cli

WORKDIR /bot

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app folder
COPY app ./app

# Run as a module
CMD ["python", "-m", "app.main"]