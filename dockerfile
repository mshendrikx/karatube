# Use Ubuntu 20.04 base image
FROM ubuntu:22.04

# Update package lists
RUN apt-get update

# Install Apache2 web server
RUN apt-get install -y python3-pip nano

WORKDIR /app

COPY requirements.txt . 

RUN pip3 install -r requirements.txt

COPY . .

# Expose port 7003 for web traffic
EXPOSE 7003

# Start Apache2 in the foreground
CMD ["python3", "/app/app.py"]