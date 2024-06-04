CREATE TABLE IF NOT EXISTS views (
    task_id UInt64,
    user_id UInt64
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'task_tracker_views',
    kafka_format = 'JSONEachRow';


CREATE TABLE IF NOT EXISTS likes (
    task_id UInt64,
    user_id UInt64
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'task_tracker_likes',
    kafka_format = 'JSONEachRow';
