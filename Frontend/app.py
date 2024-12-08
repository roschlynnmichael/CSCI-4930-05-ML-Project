import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models.user import User
from config import Config
import requests
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')

def create_app():
    app = Flask(__name__,
        static_folder=STATIC_DIR,
        static_url_path='/static',
        template_folder=os.path.join(FRONTEND_DIR, 'templates')
    )
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Update login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('login.html')

# Update register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# Add your existing routes here
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/player-database')
@login_required
def player_database():
    return render_template('player_database.html')

@app.route('/api/search-player')
@login_required
def search_player():
    """Proxy endpoint for player search"""
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'Name parameter is required'}), 400

        # Forward the request to FastAPI backend
        response = requests.get(
            f'http://localhost:8000/api/search-player',
            params={'name': name}
        )
        
        # Log the response for debugging
        print(f"FastAPI response status: {response.status_code}")
        print(f"FastAPI response content: {response.text}")
        
        return response.json(), response.status_code
        
    except requests.RequestException as e:
        print(f"Error forwarding request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_id>')
@login_required
def get_player_details(player_id):
    """Proxy endpoint for player details"""
    try:
        response = requests.get(f'http://localhost:8000/api/player/{player_id}')
        return response.json(), response.status_code
        
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player-stats/<player_id>', methods=['GET'])
@login_required
def get_player_stats(player_id):
    source = request.args.get('source')
    
    if not source:
        return jsonify({'error': 'Missing source parameter'}), 400
        
    try:
        # Forward the request to the FastAPI backend
        response = requests.get(
            f'http://localhost:8000/player-stats/{player_id}',
            params={'source': source}
        )
        return response.json(), response.status_code
        
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)