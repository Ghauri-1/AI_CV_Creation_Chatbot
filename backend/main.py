import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt


from dotenv import load_dotenv




# appp.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1245@localhost:5433/post_app"
# appp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
# dbb.init_app(app=appp)



load_dotenv()



app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
# app.secret_key = os.getenv('SECRET_KEY')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')





app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1245@localhost:5433/post_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False




bcrypt = Bcrypt(app=app)








'------------------------'


# Flask user-session part


login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please Log in to access the page: '



# Telling Flask-login how to load user from DB 
from app.storage.test_db import dbb, Users, Conversations, Messages
from backend.services.agent import run_agent

dbb.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    if request.is_json:
        return jsonify({'error': 'Login required'}), 401
    return redirect(url_for('login'))


'------------------------------------------'



# These are the Routes



@app.route('/')
def home():
        return render_template('index.html')




@app.route('/register', methods=['POST', 'GET'])
def reg():

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['em']
        password = bcrypt.generate_password_hash(request.form['pw']).decode('utf-8')


        user = Users(username=username, email=email, password=password)
        dbb.session.add(user)
        dbb.session.commit()
        return redirect(url_for('login'))
    
    
    return render_template('register.html')






@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method=='POST':
        cur_user = Users.query.filter_by(email=request.form['em']).first()


        if cur_user and bcrypt.check_password_hash(cur_user.password, request.form['pw']):
            login_user(cur_user)
            return redirect(url_for('dashboard'))
        

        else:
            return render_template('login.html', error='Invalid details, email or password')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', message='Welcome to the Dashboard!!!')



@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


@app.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'error': 'Empty message'}), 400 
    if len(msg) > 2000:
        return jsonify({'error': 'Message too long'}), 400
    try:
        reply = run_agent(current_user.email, current_user.id, msg)
        return jsonify({'reply': reply})
    except Exception as e:
        app.logger.error(f'Agent error for user {current_user.id}: {e}')
        return jsonify({'reply': 'Sorry, something went wrong. Please try again.'}), 500


@app.route('/chat/history', methods=['GET'])
@login_required
def chat_history():
    conv = (
        Conversations.query
        .filter_by(user_id=current_user.id)
        .order_by(Conversations.created_at.desc())
        .first()
    )
    if not conv:
        return jsonify([])
    msgs = (
        Messages.query
        .filter_by(conv_id=conv.conv_id)
        .order_by(Messages.timestamp.asc())
        .all()
    )
    return jsonify([{'role': m.role, 'content': m.detail} for m in msgs])


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))






if __name__=='__main__':
    with app.app_context():
        dbb.create_all()
    app.run(debug=True)