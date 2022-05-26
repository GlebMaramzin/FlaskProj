# cn5jQki0
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
from forms import LoginForm, CreateProjectForm, CreateTaskForm
from flask_socketio import SocketIO, send
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import os
from datetime import datetime


UPLOAD_FOLDER = 'userfiles'
ALLOWED_EXTENSIONS = {'txt', 'word', 'png'}
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
app.debug = True
app.config['SECRET_KEY'] = 'i3o482309g8s0d903kmmxcnvm2109349320vddfew3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cde#4rfv@localhost/flaskdb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Необходимо авторизироваться!'


@socketio.on('message')
def handle_message(data):
    send(data, broadcast=True)


def allowed_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class Project(db.Model):
    __tablename__ = 'Project'

    ProjectTitle = db.Column(db.String(100), primary_key=True)
    Desc = db.Column(db.Text(), nullable=False)
    Deadline = db.Column(db.Date(), nullable=False)
    Leader = db.Column(db.String(150), nullable=False)
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow(), nullable=False)
    IsCompleted = db.Column(db.Boolean, default=False, nullable=False)


class Role(db.Model):
    __tablename__ = 'Role'

    RoleId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(30), nullable=False)


class UserIcon(db.Model):
    __tablename__ = 'UserIcon'

    UserIconId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Path = db.Column(db.String(200), nullable=False)


class FileType(db.Model):
    __tablename__ = 'FileType'

    FileTypeId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(8), nullable=False)


class TaskStatus(db.Model):
    __tablename__ = 'TaskStatus'

    TaskStatusId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Title = db.Column(db.String(30), nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    Login = db.Column(db.String(20), primary_key=True)
    Password = db.Column(db.Text(), nullable=False)
    RoleId = db.Column(db.Integer(), db.ForeignKey('Role.RoleId'))
    UserIconId = db.Column(db.Integer(), db.ForeignKey('UserIcon.UserIconId'))
    FIO = db.Column(db.String(150), nullable=False)
    DateCreate = db.Column(db.DateTime(), default=datetime.utcnow())
    ProjectTitle = db.Column(db.String(100), db.ForeignKey('Project.ProjectTitle'))

    Role = db.relationship('Role', backref='User', uselist=False)
    Icon = db.relationship('UserIcon', backref='User', uselist=False)
    Project = db.relationship('Project', backref='User', uselist=False)

    def get_id(self):
        return self.Login


class ChatMessage(db.Model):
    __tablename__ = 'ChatMessage'

    DateTimeSend = db.Column(db.DateTime(), primary_key=True, default=datetime.utcnow())
    Login = db.Column(db.String(20), db.ForeignKey('User.Login'), primary_key=True)
    Text = db.Column(db.Text(), nullable=False)


class Task(db.Model):
    __tablename__ = 'Task'

    TaskId = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    Login = db.Column(db.String(20), db.ForeignKey('User.Login'))
    Title = db.Column(db.String(50), nullable=False)
    Desc = db.Column(db.Text, nullable=False)
    Deadline = db.Column(db.Date())
    IsPriority = db.Column(db.Boolean(), nullable=False)
    TaskStatusId = db.Column(db.Integer(), db.ForeignKey('TaskStatus.TaskStatusId'))
    DateCreate = db.Column(db.Date(), default=datetime.utcnow())
    DateComplete = db.Column(db.Date())


class TaskFile(db.Model):
    __tablename__ = 'TaskFile'

    Filename = db.Column(db.String(50), primary_key=True)
    FileTypeId = db.Column(db.Integer, db.ForeignKey('FileType.FileTypeId'))
    TaskId = db.Column(db.Integer, db.ForeignKey('Task.TaskId'))
    Path = db.Column(db.String(200), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/tasklist')
@login_required
def tasklist():
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()
    tasks = db.session.query(Task).filter(Task.Login == curr_user.Login).all()

    return render_template('tasklist.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           tasks=tasks)


@app.route('/tasklist/<int:task_id>')
@login_required
def show_task(task_id):
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()
    curr_task = db.session.query(Task).filter(Task.TaskId == task_id).first()

    return render_template('task.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           curr_task=curr_task)


@app.route('/tasklist', methods=["POST"])
@login_required
def upload_files():
    if request.method == 'POST':
        for file in request.files.getlist('file'):
            if file and allowed_files(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('create_project'))


@app.route('/project', methods=["POST", "GET"])
@login_required
def project():
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()

    if request.method == 'POST':
        return redirect(url_for('create_project'))

    return render_template('project.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           project=curr_user.Project)


@app.route('/create_project', methods=["POST", "GET"])
@login_required
def create_project():
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()
    create_project_form = CreateProjectForm()
    userlist = db.session.query(User).filter(User.Login != current_user.get_id()).all()
    if create_project_form.validate_on_submit():
        new_project = Project(
            ProjectTitle=create_project_form.title.data,
            Desc=create_project_form.desc.data,
            Deadline=create_project_form.deadline.data,
            Leader=db.session.query(User).filter(User.Login == current_user.get_id()).first().FIO
        )

        db.session.add(new_project)
        db.session.query(User).filter(User.Login == current_user.get_id()).update(
            {"ProjectTitle": create_project_form.title.data})
        db.session.commit()

        user_logins = request.form.getlist('users')
        for user_login in user_logins:
            db.session.query(User).filter(User.Login == user_login).update(
                {"ProjectTitle": create_project_form.title.data})
            db.session.commit()

        return redirect(url_for('create_task'))

    return render_template('create_project.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           form=create_project_form,
                           userlist=userlist)


@app.route('/create_task', methods=["POST", "GET"])
@login_required
def create_task():
    create_task_form = CreateTaskForm()
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()

    userlist = db.session.query(User).filter(User.Project != None).all()

    if create_task_form.validate_on_submit():
        new_task = Task(
            Login=request.form.getlist('users')[0],
            Title=create_task_form.title.data,
            Desc=create_task_form.desc.data,
            Deadline=create_task_form.deadline.data,
            IsPriority=create_task_form.isPriority.data,
            TaskStatusId=2
        )

        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("create_task"))

    return render_template('create_task.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           form=create_task_form,
                           userlist=userlist)


@app.route('/repository')
@login_required
def repository():
    return render_template('repository.html')


@app.route('/teamchat')
@login_required
def teamchat():
    curr_user = db.session.query(User).filter(User.Login == current_user.get_id()).first()

    return render_template('teamchat.html',
                           user_fio=curr_user.FIO,
                           user_role=curr_user.Role.Title,
                           user_img=curr_user.Icon.Path,
                           project=curr_user.Project)


@app.route('/', methods=["POST", "GET"])
def login():
    # if current_user.is_authenticated:
    #    return redirect(url_for('tasklist'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.query(User).filter(User.Login == login_form.login.data).first()
        if user and check_password_hash(user.Password, login_form.password.data):
            login_user(user)
            return redirect(url_for('tasklist'))

    return render_template('login.html', form=login_form)


if __name__ == '__main__':
    app.run()
