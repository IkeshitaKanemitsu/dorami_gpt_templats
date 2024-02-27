import os
import faiss
import numpy as np
from flask import Flask, flash, url_for, redirect, render_template, jsonify, request
from flask_wtf import FlaskForm
from wtforms import ValidationError, StringField, PasswordField, SubmitField, DateField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
import pytz
from sqlalchemy.schema import Column
from sqlalchemy import Integer, String, Float, Text
from study.read_pdf import to_vec
from study.read_web import read_web
from chat.qachat import qa
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

app = Flask(__name__)

database_file = os.path.join(os.path.abspath(os.getcwd()), 'user.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+database_file
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

class Staff(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staffname = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(18))
    email = db.Column(db.String(64), unique=True, index=True)
    api_key = db.Column(db.String(40))
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(64))
    
class Conv_log(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qry = db.Column(db.String(200))
    res = db.Column(db.String(1000))
    pub_date = db.Column(db.DateTime, nullable=False,
                                default=datetime.datetime.now(pytz.timezone('Asia/Tokyo')))
    

if os.path.exists('/home/ubuntu/user.db') == False:
    with app.app_context():
        db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/signup/')

@login_manager.user_loader
def load_user(user_id):
    return Staff.query.get(int(user_id))

@app.route('/')
def top():
    # staffname = ""
    # username = ""
    # user = User(username=username)
    # db.session.add(user)
    # db.session.commit()
    # staff = Staff(staffname=staffname)
    # db.session.add(staff)
    # db.session.commit()

    return render_template("index.html")

@app.route('/home/')
# @login_required
def home():
    user = User.query.order_by(User.id.desc()).first()
    date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    qry = " "
    res = " "
    conv_log = Conv_log(qry=qry, res=res, pub_date=date)
    db.session.add(conv_log)
    db.session.commit()
    
    return render_template("index2.html")

@app.route('/home_staff/')
@login_required
def home_staff():
    chat_user = current_user.staffname
    date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    qry = " "
    res = " "
    conv_log = Conv_log(qry=qry, res=res, pub_date=date)
    db.session.add(conv_log)
    db.session.commit()
    
    return render_template("index3.html", chat_user=chat_user)

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        staffname = request.form.get('staffname')
        password = request.form.get('password')
        # email = request.form.get('email')
        # apikey = request.form.get('apikey')

        # user = User(username=username, password=generate_password_hash(password, method='sha256'))
        staff = Staff(staffname=staffname, password=password)
        db.session.add(staff)
        db.session.commit()
        return redirect('/login/')
    else:
        return render_template('signup.html')
    
@app.route('/signup_user/', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        username = request.form.get('username')
        # password = request.form.get('password')
        # email = request.form.get('email')
        # apikey = request.form.get('apikey')

        # user = User(username=username, password=generate_password_hash(password, method='sha256'))
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
        return render_template('index2.html')
    else:
        return render_template('signup_user.html')
    
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staffname = request.form.get('staffname')
        password = request.form.get('password')

        staff = Staff.query.filter_by(staffname=staffname).first()
        if not staff:
            return render_template('login.html', error_message='登録されていません。')
        if staff.password == password:
            login_user(staff)
            return redirect('/home_staff')
        else:
            return render_template('login.html', error_message='パスワードが違います。')
    else:
        return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/login/') 

@app.route('/study/')
@login_required
def study():
   return render_template("study.html") 

@app.route('/study_web/')
@login_required
def study_web():
   return render_template("study_web.html") 

@app.route('/read_web/', methods = ['GET', 'POST'])
@login_required
def web_data_loader():
    if request.method == 'POST':
        get_url = request.form.get('read_url')
        db2 = read_web(get_url)
        embedding = OpenAIEmbeddings(
        model="text-embedding-ada-002"
        )
        db2.save_local("/home/ubuntu/venv/venv/faiss_db") 
        return redirect(url_for('study_web')) 

@app.route('/study_pdf/')
@login_required
def upload_file():
   return render_template("upload.html")
	
@app.route('/uploader/', methods = ['GET', 'POST'])
@login_required
def uploader():
    if request.method == 'POST':
      f = request.files['file']
      f_name = '/home/ubuntu/venv/venv/article/'+f.filename
      f.save(f_name)
      db = to_vec(f_name)
      if os.path.exists('/home/ubuntu/venv/venv/faiss_db') == False:
        db.save_local("/home/ubuntu/venv/venv/faiss_db")
      else:
        embedding = OpenAIEmbeddings(
        model="text-embedding-ada-002"
        )
        db2 = FAISS.load_local("/home/ubuntu/venv/venv/faiss_db", embedding)
        db2.merge_from(db)
        db2.save_local("/home/ubuntu/venv/venv/faiss_db") 
        return redirect(url_for('upload_file'))


@app.route('/history/')
@login_required
def history():
    c_logs = Conv_log.query.order_by(Conv_log.id.desc())
    return render_template("history.html", c_logs=c_logs)


@app.route('/chat/', methods=["GET", "POST"])
# @login_required
def chat():
    if request.method == 'GET':
        user = User.query.order_by(User.id.desc()).first()
        
        c_log = Conv_log.query.order_by(Conv_log.id.desc()).first()
        return render_template("chat.html", c_log=c_log, user=user)
        
    else:
        date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
        qry = request.form['question']
        res = qa(qry)
        conv_log = Conv_log(qry=qry, res=res, pub_date=date)
        db.session.add(conv_log)
        db.session.commit()
        return redirect(url_for("chat"))
    
@app.route('/chat_staff/', methods=["GET", "POST"])
@login_required
def chat_staff():
    if request.method == 'GET':
        user = User.query.order_by(User.id.desc()).first()
        chat_user = current_user.staffname
        c_log = Conv_log.query.order_by(Conv_log.id.desc()).first()
        return render_template("chat_staff.html", c_log=c_log, chat_user=chat_user)
        
    else:
        date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
        chat_user = current_user.staffname
        qry = request.form['question']
        res = qa(qry)
        conv_log = Conv_log(qry=qry, res=res, pub_date=date)
        db.session.add(conv_log)
        db.session.commit()
        return redirect(url_for("chat_staff"))
  
if __name__ == "__main__":
    # app.run(host="54.249.152.255", debug=False)
    app.run(debug=True)