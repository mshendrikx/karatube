# Use Ubuntu 20.04 base image
FROM ubuntu:22.04

# Update package lists
RUN apt-get update

# Install Apache2 web server
RUN apt-get install -y python3-pip

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

# Expose port 80 for web traffic
EXPOSE 5000

# Start Apache2 in the foreground
CMD ["python3", "/app/app.py"]