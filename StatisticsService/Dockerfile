FROM python:3.10

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional

# Create a directory for the application
RUN mkdir /StatisticsService
WORKDIR /StatisticsService

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt
RUN pip3 install --upgrade "protobuf<=3.20.1"
# Copy the Protos folder and generated Python files
COPY ./Protos /StatisticsService/Protos

COPY ./stat_service.py /StatisticsService

# Expose port 50051 (default gRPC port)
EXPOSE 50052

CMD ["python3", "stat_service.py"]