import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')

from flask import Flask, render_template, send_from_directory
from flask_assets import Environment, Bundle

app = Flask(__name__,
    static_folder=STATIC_DIR,
    static_url_path='/static',
    template_folder=os.path.join(FRONTEND_DIR, 'templates')
)

# Initialize Flask-Assets
assets = Environment(app)

# Define Tailwind CSS bundle
css = Bundle(
    'css/main.css',
    filters='postcss',
    output='css/tailwind.css'
)
assets.register('css_all', css)

# Add route for serving animations directly
@app.route('/static/animations/<path:filename>')
def serve_animation(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'animations'), filename)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

if __name__ == '__main__':
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Frontend Dir: {FRONTEND_DIR}")
    print(f"Static Dir: {STATIC_DIR}")
    app.run(debug=True)