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

# Generate crontab content directly in the Dockerfile
RUN echo "* * * * * python3 /app/karatubed.py" > /etc/cron.d/karatubed-cron

# Set permissions
RUN chmod 0644 /etc/cron.d/karatubed-cron

# Expose port 7003 for web traffic
EXPOSE 7003

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]