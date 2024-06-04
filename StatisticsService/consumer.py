from kafka import KafkaConsumer
from clickhouse_driver import Client
import time
import json

time.sleep(10)

consumer = KafkaConsumer('task_tracker',
                         bootstrap_servers='kafka:29092',
                         value_deserializer=lambda v: json.loads(v.decode('utf-8')))

client = Client(host='stats_db', port='9000')
client.execute(
    'CREATE TABLE IF NOT EXISTS views (task_id UInt64, user_id UInt64) ENGINE MergeTree ORDER BY (task_id, user_id)')
client.execute(
    'CREATE TABLE IF NOT EXISTS likes (task_id UInt64, user_id UInt64) ENGINE MergeTree ORDER BY (task_id, user_id)')

for msg in consumer:
    data = msg.value
    msg_type = int(data['msg_type'])
    task_id = int(data['task_id'])
    user_id = int(data['user_id'])
    print(f'Message data: {data}')

    if msg_type == 1:
        client.execute('INSERT INTO views (task_id, user_id) VALUES',
                       [[task_id, user_id]])
    elif msg_type == 1:
        client.execute('INSERT INTO likes (task_id, user_id) VALUES',
                       [[task_id, user_id]])
