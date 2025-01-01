# Use Ubuntu 22.04 base image
FROM ubuntu:22.04

# Install packages
RUN apt-get update && apt-get install -y python3-pip apt-transport-https nano curl cron

RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt . 

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . .

RUN mv karatubed_cron /etc/cron.d/

RUN chmod 0644 /etc/cron.d/karatubed_cron

RUN crontab /etc/cron.d/karatubed_cron

RUN chmod +x /app/karatubed.sh

RUN mkdir logs

# Expose port 7003 for web traffic
EXPOSE 7003

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]