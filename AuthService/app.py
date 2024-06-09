from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import jwt
import grpc
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from proto_to_dict import proto_to_dict
from kafka import KafkaProducer

from Protos.auth_service_pb2 import *
from Protos.auth_service_pb2_grpc import *
from StatProto.stat_service_pb2 import *
from StatProto.stat_service_pb2_grpc import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@auth_db/auth_db'
db = SQLAlchemy(app)

app.app_context().push()

# Configure gRPC channel
channel = grpc.insecure_channel("task_service:50051")
task_client = TaskServiceStub(channel)

statistics_channel = grpc.insecure_channel("stats_service:50052")
statistics_client = StatisticServiceStub(statistics_channel)

KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
KAFKA_TOPIC = 'task_tracker'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(2, 0, 2)
)


def generate_token(user):
    token = jwt.encode({'user_id': str(user.id)}, str(app.config['SECRET_KEY']), algorithm='HS256')
    user.token = token
    db.session.commit()
    return token


def check_token(token):
    try:
        decoded_token = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms=['HS256'])
        user_id = int(decoded_token['user_id'])
        return user_id
    except jwt.ExpiredSignatureError:
        return "Expired token. Please log in again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please log in again."


class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(1024), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    birthdate = db.Column(db.Date)
    email = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    token = db.Column(db.String(1024))


# Регистрация нового пользователя
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    password_hash = generate_password_hash(data['password'])
    if db.session.query(UserData).filter(UserData.username == data['username']).first():
        return jsonify({'message': 'User with this username already exists'}), 400
    new_user = UserData(username=data['username'], password_hash=password_hash,
                        first_name=data.get('first_name'), last_name=data.get('last_name'),
                        birthdate=data.get('birthdate'), email=data.get('email'),
                        phone_number=data.get('phone_number'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


# Обновление данных пользователя
@app.route('/update', methods=['PUT'])
def update_user():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    user = db.session.query(UserData).get(user_id)
    data = request.json
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.birthdate = datetime.strptime(data.get('birthdate', str(user.birthdate)), '%d.%m.%Y').date()
    user.email = data.get('email', user.email)
    user.phone_number = data.get('phone_number', user.phone_number)

    db.session.commit()
    return jsonify({'message': 'User updated successfully'})


# Аутентификация пользователя
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    username = data['username']
    password = data['password']

    user = UserData.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        token = generate_token(user)
        user.token = token
        db.session.commit()
        return jsonify({'message': 'Login successful', 'token': token})
    else:
        return jsonify({'message': 'Login failed'})


@app.route('/logout', methods=['POST'])
def logout_user():
    token = request.headers.get('Authorization')
    user_id = check_token(token)
    user = db.session.query(UserData).get(user_id)
    if user:
        user.token = None
        db.session.commit()
        return jsonify({'message': 'Logout successful'})
    else:
        return jsonify({'message': 'Logout failed'})


# Task API methods with JWT authorization

@app.route('/create_task', methods=['POST'])
def create_task():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    print(type(user_id))
    data = request.json
    task_request = CreateTaskRequest(
        title=data['title'],
        description=data['description'],
        author_id=user_id
    )
    response = task_client.CreateTask(task_request)
    if response.status not in range(200, 300):
        return jsonify({'message': f'RPC error: {response}'}), response.status
    return jsonify({'message': f'Task with id {response.task.id} created'}), 200


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    data = request.json
    upd_request = UpdateTaskRequest(
        id=task_id,
        title=data['title'],
        description=data['description'],
        author_id=user_id,
        completed=data['completed']
    )

    response = task_client.UpdateTask(upd_request)
    if response.status not in range(200, 300):
        return jsonify({'message': f'RPC error: {response}'}), response.status
    return jsonify({'message': f'Task with id {response.task.id} updated'}), 200


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    del_request = DeleteTaskRequest(
        id=task_id,
        author_id=user_id
    )
    response = task_client.DeleteTask(del_request)
    if response.status not in range(200, 300):
        return jsonify({'message': f'RPC error: {response}'}), response.status
    return jsonify({'message': f'Task with id {response.task.id} deleted'}), 200


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    get_request = GetTaskRequest(id=task_id)
    response = task_client.GetTask(get_request)
    if response.status not in range(200, 300):
        return jsonify({'message': f'RPC error: {response}'}), response.status
    return jsonify({'task': proto_to_dict(response.task)}), 200


@app.route('/tasks', methods=['GET'])
def list_tasks():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('page_size', 5, type=int)
    list_request = ListTasksRequest(
        page=page,
        per_page=per_page)
    response = task_client.ListTasks(list_request)
    if response.status not in range(200, 300):
        return jsonify({'message': f'RPC error: {response}'}), response.status
    return jsonify({'count': response.total_count,
                    'tasks': [proto_to_dict(task) for task in response.tasks]}), 200


@app.route('/task/view/<int:task_id>', methods=['PUT'])
def view_task(task_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    get_request = GetTaskRequest(id=task_id)
    response = task_client.GetTask(get_request)
    if response.status not in range(200, 300):
        return jsonify({'message': 'Invalid task'}), 400
    data = {'msg_type': 1, 'task_id': task_id, 'user_id': user_id}
    producer.send(KAFKA_TOPIC, data)
    return jsonify({'View sent to kafka': data}), 200


@app.route('/task/like/<int:task_id>', methods=['PUT'])
def like_task(task_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user_id = check_token(token)
    get_request = GetTaskRequest(id=task_id)
    response = task_client.GetTask(get_request)
    if response.status not in range(200, 300):
        return jsonify({'message': 'Invalid task'}), 400
    data = {'msg_type': 2, 'task_id': task_id, 'user_id': user_id}
    producer.send(KAFKA_TOPIC, data)
    return jsonify({'Like sent to kafka': data}), 200


@app.route('/tasks/<int:task_id>/statistics', methods=['GET'])
def get_task_statistics(task_id):
    try:
        response = statistics_client.GetTaskStatistic(TaskStatRequest(id=task_id))
        return jsonify({'likes': response.likes, 'views': response.views}), 200
    except grpc.RpcError as e:
        return jsonify({'message': f'Error getting task statistics: {e}'}), 500


@app.route('/tasks/popular/<sort_type>', methods=['GET'])
def get_popular_tasks(sort_type):
    try:
        response = statistics_client.GetPopularTask(PopularTaskRequest(sort_type=sort_type))
        tasks = [{'id': task.id, 'author_id': task.author_id, 'count': task.count} for task in response.popular_tasks]
        return jsonify({'popular_tasks': tasks}), 200
    except grpc.RpcError as e:
        return jsonify({'message': f'Error getting popular tasks: {e}'}), 500


@app.route('/users/popular', methods=['GET'])
def get_popular_users():
    try:
        response = statistics_client.GetPopularUser(Empty())
        users = [{'author_id': user.author_id, 'likes': user.likes} for user in response.popular_users]
        return jsonify({'popular_users': users}), 200
    except grpc.RpcError as e:
        return jsonify({'message': f'Error getting popular users: {e}'}), 500


if __name__ == '__main__':
    db.create_all()
    app.run(port=8000, host="0.0.0.0", debug=True)
