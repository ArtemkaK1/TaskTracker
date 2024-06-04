FROM python:3.10

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional

# Create a directory for the application
RUN mkdir /TaskService
WORKDIR /TaskService

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt
RUN pip3 install --upgrade "protobuf<=3.20.1"
# Copy the Protos folder and generated Python files
COPY ./Protos /TaskService/Protos

# Copy the tasks_server.py file
COPY ./tasks_service.py /TaskService
COPY ./tasks_model.py /TaskService

# Expose port 50051 (default gRPC port)
EXPOSE 50051

# Copy the wait-for-db.sh script
COPY wait-for-db.sh /TaskService/wait-for-db.sh

# Set execute permissions for the script
RUN chmod +x /TaskService/wait-for-db.sh

# Update the CMD instruction to use the wait-for-db.sh script
CMD ["/TaskService/wait-for-db.sh", "tasks_db", "5432", "python3", "tasks_service.py"]