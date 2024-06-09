FROM python:3.10

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional

# Create a directory for the application
RUN mkdir /AuthService
WORKDIR /AuthService

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt
RUN pip3 install --upgrade "protobuf<=3.20.1"
# Copy the Protos folder and generated Python files
COPY ./Protos /AuthService/Protos
COPY ./StatProto /AuthService/StatProto

COPY ./app.py /AuthService
COPY ./proto_to_dict.py /AuthService

# Expose port 8000
EXPOSE 8000

# Copy the wait-for-db.sh script
COPY wait-for-db.sh /AuthService/wait-for-db.sh

# Set execute permissions for the script
RUN chmod +x /AuthService/wait-for-db.sh

# Update the CMD instruction to use the wait-for-db.sh script
CMD ["/AuthService/wait-for-db.sh", "auth_db", "5432", "python3", "app.py"]