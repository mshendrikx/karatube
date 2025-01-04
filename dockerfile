# Use Ubuntu 22.04 base image
FROM ubuntu:22.04

# Install packages
# python3-tk python3-dev xvfb chromium-browser chromium-chromedriver 
RUN apt-get update && apt-get install -y python3-pip apt-transport-https nano curl cron
ENV TZ=America/Sao_Paulo
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt . 

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir logs

# Expose port 7003 for web traffic
EXPOSE 7003

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]