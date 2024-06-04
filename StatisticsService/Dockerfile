FROM python:3.10

WORKDIR /StatisticsService

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY consumer.py .
CMD ["python3", "consumer.py"]