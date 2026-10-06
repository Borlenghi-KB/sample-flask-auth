import bcrypt
from flask import Flask, jsonify, request
from models.user import User
from databese import db
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin123@localhost:3306/flask-crud'

login_manager = LoginManager()

db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if (username or email) and password:
        user = User.query.filter((User.username == username) | (User.email == email)).first()

        if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
            login_user(user)
            print(current_user.is_authenticated)
            return jsonify({'message': 'Login successful'})
            
    return jsonify({'message': 'Invalid username or password'}), 400

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})

@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if username and email and password:
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400
        
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        new_user = User(username=username, email=email, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'})

    return jsonify({'message': 'Missing required fields'}), 400

@app.route('/user/<int:id>', methods=['GET'])
@login_required
def read_user(id):
    user = User.query.get(id)
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'email': user.email})
    return jsonify({'message': 'User not found'}), 404

@app.route('/user/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    user = User.query.get(id)
    if id != current_user.id and current_user.role != 'admin':
        return jsonify({'message': 'You can only update your own account'}), 403
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.password = data.get('password', user.password)

    db.session.commit()
    return jsonify({'message': 'User updated successfully'})


@app.route('/user/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    user = User.query.get(id)
    if current_user.role != 'admin' and id != current_user.id:
        return jsonify({'message': 'You can only delete your own account'}), 403
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if id != current_user.id:
        return jsonify({'message': 'You can only delete your own account'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)