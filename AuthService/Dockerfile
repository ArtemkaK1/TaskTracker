FROM python:3.10

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional

# Create a directory for the application
RUN mkdir /my-app
COPY ./app.py /my-app
WORKDIR /my-app

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

# Expose port 8000
EXPOSE 8000

# Copy the wait-for-db.sh script into the container
COPY wait-for-db.sh /my-app/wait-for-db.sh

# Set execute permissions for the script
RUN chmod +x /my-app/wait-for-db.sh

# Update the CMD instruction to use the wait-for-db.sh script
CMD ["/my-app/wait-for-db.sh", "db", "5432", "python3", "app.py"]

