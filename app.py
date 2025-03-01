from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["MONGO_URI"] = "mongodb://localhost:27017/kamusic"
mongo = PyMongo(app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password = password

@login_manager.user_loader
def load_user(username):
    user = mongo.db.users.find_one({"username": username})
    if user:
        return User(user["username"], user["password"])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if mongo.db.users.find_one({"username": username}):
            flash("Username already exists!")
        else:
            mongo.db.users.insert_one({"username": username, "password": password})
            flash("Registration successful!")
            return redirect(url_for("login"))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({"username": username, "password": password})
        if user:
            login_user(User(username, password))
            return redirect(url_for("dashboard"))
        flash("Invalid credentials!")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route('/dashboard')
@login_required
def dashboard():
    musics = list(mongo.db.musics.find())
    return render_template('dashboard.html', musics=musics)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_music():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            mongo.db.musics.insert_one({
                "title": request.form['title'],
                "artist": request.form['artist'],
                "genre": request.form['genre'],
                "filename": filename,
                "upload_date": datetime.utcnow()
            })
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/musics')
def list_musics():
    musics = list(mongo.db.musics.find())
    return render_template('musics.html', musics=musics)

@app.route('/blog', methods=['GET', 'POST'])
def blog():
    if request.method == 'POST':
        mongo.db.blog_posts.insert_one({
            "title": request.form['title'],
            "content": request.form['content'],
            "author": request.form['author'],
            "created_at": datetime.utcnow()
        })
    posts = list(mongo.db.blog_posts.find())
    return render_template('blog.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
