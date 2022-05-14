import sys

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from forms import LoginForm, CreateProjectForm, CreateTaskForm
from werkzeug.utils import secure_filename
import os
from datetime import datetime


UPLOAD_FOLDER = 'userfiles'
ALLOWED_EXTENSIONS = {'txt', 'word', 'png'}

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'i3o482309g8s0d903kmmxcnvm2109349320vddfew3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cde#4rfv@localhost/flaskdb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Необходимо авторизироваться!'


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class Project(db.Model):
    __tablename__ = 'Project'

    ProjectId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(100), nullable=False)
    Desc = db.Column(db.Text, nullable=False)
    Deadline = db.Column(db.Date(), nullable=False)
    Leader = db.Column(db.String(250), nullable=False)
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow(), nullable=False)
    IsEnd = db.Column(db.Boolean, default=False, nullable=False)


class Role(db.Model):
    __tablename__ = 'Role'

    RoleId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(30), nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    UserId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Login = db.Column(db.String(12), nullable=False)
    Password = db.Column(db.Text(), nullable=False)
    FIO = db.Column(db.String(250), nullable=False)
    RoleId = db.Column(db.Integer(), db.ForeignKey('Role.RoleId'))
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow())
    ProjectId = db.Column(db.Integer(), db.ForeignKey('Project.ProjectId'))

    Role = db.relationship('Role', backref='User', uselist=False)

    def get_id(self):
        return self.UserId


class TaskStatus(db.Model):
    __tablename__ = 'TaskStatus'

    TaskStatusId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(30), nullable=False)


class Task(db.Model):
    __tablename__ = 'Task'

    TaskId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ProjectId = db.Column(db.Integer(), db.ForeignKey('Project.ProjectId'))
    Title = db.Column(db.String(50), nullable=False)
    Desc = db.Column(db.Text, nullable=False)
    Deadline = db.Column(db.Date())
    IsPriority = db.Column(db.Boolean(), nullable=False)
    TaskStatusId = db.Column(db.Integer(), db.ForeignKey('TaskStatus.TaskStatusId'))
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow())


class Repository(db.Model):
    __tablename__ = 'Repository'

    RepositoryId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ProjectId = db.Column(db.Integer(), db.ForeignKey('Project.ProjectId'))
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow())


class RepositoryFile(db.Model):
    __tablename__ = 'RepositoryFile'

    RepositoryFileId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Path = db.Column(db.String(200), nullable=False)
    RepositoryId = db.Column(db.Integer(), db.ForeignKey('Repository.RepositoryId'))
    DateLoad = db.Column(db.DateTime(), default=datetime.utcnow())


class ChatMessage(db.Model):
    __tablename__ = 'ChatMessage'

    ChatMessageId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer(), db.ForeignKey('User.UserId'))
    Text = db.Column(db.Text(), nullable=False)
    DateSend = db.Column(db.DateTime(), default=datetime.utcnow())
    ProjectId = db.Column(db.Integer(), db.ForeignKey('Project.ProjectId'))


def allowed_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/tasklist')
@login_required
def tasklist():
    curr_user = db.session.query(User).filter(User.UserId == current_user.get_id()).first()

    return render_template('tasklist.html', user_fio=curr_user.FIO, user_role=curr_user.Role.Title)


@app.route('/tasklist', methods=["POST"])
@login_required
def upload_files():
    if request.method == 'POST':
        for file in request.files.getlist('file'):
            if file and allowed_files(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('create_project'))


@app.route('/project')
@login_required
def project():
    return render_template('project.html')


@app.route('/create_project', methods=["POST", "GET"])
@login_required
def create_project():
    create_project_form = CreateProjectForm()
    userlist = db.session.query(User).all()
    if create_project_form.validate_on_submit():
        developers_id = request.form.getlist('users')
        print(create_project_form.title.data, file=sys.stderr)
        print(developers_id, file=sys.stderr)
        d = []
        #for id in developers_id:
            #d.append(db.session.query(User).filter().first())
        return redirect(url_for('create_task'))

    return render_template('create_project.html', form=create_project_form, userlist=userlist)


@app.route('/create_task')
@login_required
def create_task(developerlist):
    create_task_form = CreateTaskForm()

    return render_template('create_task.html', form=create_task_form)


@app.route('/repository')
@login_required
def repository():
    return render_template('repository.html')


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


@app.route('/', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasklist'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.query(User).filter(User.Login == login_form.login.data).first()
        if user and user.Password == login_form.password.data:
            login_user(user)
            return redirect(url_for('tasklist'))

        flash('Poshel hanui')
    return render_template('login.html', form=login_form)


if __name__ == '__main__':
    app.run()
