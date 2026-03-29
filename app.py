from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random, requests, os

app = Flask(__name__)
app.secret_key = 'royal_games_777_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///royalgames.db'
db = SQLAlchemy(app)

# --- CONFIG ---
BOT_TOKEN = "8602301777:AAEQKw6atB6GNE8v0q8Li-qsXso7m7xxiRw"
ADMIN_CHAT_ID = "0952779456" 

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=500.0)
    is_admin = db.Column(db.Boolean, default=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20)) 
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.now())

with app.app_context():
    db.create_all()

# --- ROUTES ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/spin', methods=['POST'])
def spin():
    user = User.query.get(session['user_id'])
    if user.balance < 10: return jsonify({"error": "Low Balance"}), 400
    user.balance -= 10
    res = [random.choice(["🍒", "🍋", "7️⃣"]) for _ in range(3)]
    win = 100 if res[0]==res[1]==res[2]=="7️⃣" else 0
    user.balance += win
    db.session.add(Transaction(user_id=user.id, type="Spin", amount=10))
    if win > 0: 
        db.session.add(Transaction(user_id=user.id, type="Win", amount=win))
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_CHAT_ID}&text=🎰 {user.username} WON {win} ETB!")
    db.session.commit()
    return jsonify({"result": res, "win": win, "balance": user.balance})

if __name__ == '__main__':
    app.run(debug=True)
