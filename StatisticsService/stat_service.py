import grpc
import time
import json
from concurrent import futures
from kafka import KafkaConsumer
from threading import Thread

from Protos.stat_service_pb2 import *
from Protos.stat_service_pb2_grpc import *

from clickhouse_driver import Client

CLICKHOUSE_HOST = 'stats_db'
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DATABASE = 'default'


time.sleep(10)

consumer = KafkaConsumer('task_tracker',
                         bootstrap_servers='kafka:29092',
                         value_deserializer=lambda v: json.loads(v.decode('utf-8')))

client = Client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)
client.execute(
    'CREATE TABLE IF NOT EXISTS views (task_id UInt64, user_id UInt64) ENGINE MergeTree ORDER BY (task_id, user_id)')
client.execute(
    'CREATE TABLE IF NOT EXISTS likes (task_id UInt64, user_id UInt64) ENGINE MergeTree ORDER BY (task_id, user_id)')


def consume_from_kafka():
    for msg in consumer:
        data = msg.value
        msg_type = int(data['msg_type'])
        task_id = int(data['task_id'])
        user_id = int(data['user_id'])
        print(f'Message data: {data}')

        if msg_type == 1:
            client.execute('INSERT INTO views (task_id, user_id) VALUES',
                           [[task_id, user_id]])
        elif msg_type == 2:
            client.execute('INSERT INTO likes (task_id, user_id) VALUES',
                           [[task_id, user_id]])


class StatisticService(StatisticServiceServicer):

    def __init__(self):
        self.clickhouse_client = Client(host=CLICKHOUSE_HOST,
                                        port=CLICKHOUSE_PORT,
                                        database=CLICKHOUSE_DATABASE)

    def GetTaskStatistic(self, request, context):
        task_id = request.id

        likes = self.clickhouse_client.execute(
            f"SELECT count(*) FROM likes WHERE task_id = {task_id}"
        )[0][0]
        views = self.clickhouse_client.execute(
            f"SELECT count(*) FROM views WHERE task_id = {task_id}"
        )[0][0]

        return TaskStatResponse(likes=likes, views=views)

    def GetPopularTask(self, request, context):
        sort_type = request.sort_type
        if sort_type not in ["likes", "views"]:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid sort type.")

        query = f"""
        SELECT task_id, count(*) AS cnt
        FROM {sort_type}
        GROUP BY task_id
        ORDER BY cnt DESC
        LIMIT 5
        """
        result = self.clickhouse_client.execute(query)

        popular_tasks = [TaskRsp(id=row[0], count=row[1]) for row in result]

        return PopularTaskResponse(popular_tasks=popular_tasks)

    def GetPopularUser(self, request, context):
        query = """
        SELECT user_id, count(*) AS cnt
        FROM likes
        GROUP BY user_id
        ORDER BY cnt DESC
        LIMIT 3
        """
        result = self.clickhouse_client.execute(query)

        popular_users = [UserRsp(author_id=row[0], likes=row[1]) for row in result]

        return PopularUserResponse(popular_users=popular_users)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_StatisticServiceServicer_to_server(StatisticService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    kafka_thread = Thread(target=consume_from_kafka)
    kafka_thread.start()
    serve()
