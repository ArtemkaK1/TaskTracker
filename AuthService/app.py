from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@db:5432/tracker_users'
db = SQLAlchemy(app)

app.app_context().push()


def generate_token(user):
    token = jwt.encode({'user_id': str(user.id)}, str(app.config['SECRET_KEY']), algorithm='HS256')
    user.token = token
    db.session.commit()
    return token


def check_token(token):
    try:
        decoded_token = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms='HS256')
        user_id = int(decoded_token['user_id'])
        user = UserData.query.get(user_id)
        if user and user.token == token:
            return user
        else:
            return jsonify({'message': 'User does not exist'})
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return jsonify({'message': 'User token is invalid'})


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
    new_user = UserData(username=data['username'], password_hash=password_hash,
                     first_name=data.get('first_name'), last_name=data.get('last_name'),
                     birthdate=data.get('birthdate'), email=data.get('email'),
                     phone_number=data.get('phone_number'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


# Обновление данных пользователя
@app.route('/update/', methods=['PUT'])
def update_user():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token not provided'}), 401
    user = check_token(token)
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
    user = check_token(token)
    if user:
        user.token = None
        db.session.commit()
        return jsonify({'message': 'Logout successful'})
    else:
        return jsonify({'message': 'Logout failed'})


if __name__ == '__main__':
    db.create_all()
    app.run(port=8000, host="0.0.0.0", debug=True)

