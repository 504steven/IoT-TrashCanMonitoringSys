#!venv/bin/python
import os
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from flask_admin import BaseView, expose
from flask_socketio import SocketIO, emit, send, Namespace, join_room, leave_room
from flask_pymongo import PyMongo
import sendEmail

# Create Flask application
app = Flask(__name__)
socketio = SocketIO(app)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

app.config["MONGO_DBNAME"] = "GarbageCanIoT"
app.config["MONGO_URI"] = "mongodb://localhost:27017/GarbageCanIoT"
mongo = PyMongo(app)
sensor_data = mongo.db.sensor_data
sensor_data.create_index( [('time', 1)])
nextId = 1
client_id_noticed = set()

# python clients (trash cans)
devices = []

# web view
viewers = []

# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


    # can_edit = True
    edit_modal = True
    create_modal = True
    can_export = True
    can_view_details = True
    details_modal = True

class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    # form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list


class CustomView(BaseView):
    @expose('/')
    def index(self):
        user_id = str(current_user)
        device_count = len(devices)
        single_cost = 50
        total_cost = device_count * single_cost
        obj = {"user_id":user_id,"device_count":device_count, "single_cost":single_cost, "total_cost":total_cost}
        return self.render('admin/payment.html',obj=obj)

# Flask views
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route("/")
def index():
    return redirect(url_for('admin.index'))


# Create admin
admin = flask_admin.Admin(
    app,
    'Trashtracker',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(Role, db.session, menu_icon_type='fa', menu_icon_value='fa-server', name="Roles"))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(CustomView(name="Billing", endpoint='billing', menu_icon_type='fa', menu_icon_value='fa-connectdevelop',))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        test_user = user_datastore.create_user(
            first_name='Admin',
            email='admin',
            password=encrypt_password('admin'),
            roles=[user_role, super_user_role]
        )

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]
        last_names = [
            'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
            'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
            'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
        ]

        for i in range(len(first_names)):
            tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=encrypt_password(tmp_pass),
                roles=[user_role, ]
            )
        db.session.commit()
    return

@socketio.on('message')
def handle_message(message):
    print("got message from {} : {}".format(request.namespace,message))

    send(message)

@socketio.on("heartbeat")
def handle_heartbeat(message):
    print(message)
    pass

@socketio.on('ui_request')
def handle_ui_request(message):
    print("got message from {} : {}".format(request.namespace,message))


# @socketio.on('json')
# def handle_json(json):
#     send(json, json=True)


@socketio.on('init_viewer')
def handle_init_viewer(json):
    print("init viewer",request.sid)
    join_room(request.sid)
    viewers.append(request.sid)


@socketio.on("get_reading")
def handle_get_readings(data):
    print("get readings request",data)
    for d in devices:
        print("sending to",d)
        emit("get_reading",room=d)

@socketio.on("return_data")
def handle_return_data(data):
    print("returning data to browser:",data)
    # notify users via email
    global client_id_noticed
    #print(data['percentage'], data['percentage']>0.8, client_id_noticed.add( data['id']))
    if data['percentage'] >= 0.8 and data['id'] not in client_id_noticed:
        client_id_noticed.add(data['id'])
        print("Percentage higher than 0.8, sending email", type(data['id']))
        sendEmail.sendemail("Dear {}, your garbage can, id={}, is above 80% full. Please plan for collection.".format(current_user, data['id'][-1]) )
    if data['percentage'] < 0.8 and data['id'] in client_id_noticed:
        client_id_noticed.remove(data['id'])

    for v in viewers:
        emit("return_data",data,room=v)
    sensor_data.insert_one(data)


@socketio.on("return_reading")
def handle_return_reading(data):
    print("returning data to browser:",data)
    # notify users via email
    if data['percentage'] >= 0.8:
        print("Percentage higher than 0.8, sending email")
        sendEmail.sendemail("Dear {}, your garbage can is getting to 80% full.".format(current_user))
    for v in viewers:
        emit("return_data",data,room=v)
   
 
@socketio.on("query_data")  ###########
def handle_query_data(data):
    print("received query:", data['start_time'])
    res = sensor_data.find({
    "time": {
        "$gt": data['start_time'],
        "$lte": data['end_time']
    }}, {'_id':0} ).sort([("time",1)]);


    # update = True    #### lock??  [{'k':1},{'k':2}]
    data_to_send = {'sensor_data': list(res)}
    print("data to send - size:", res.count(), " - data:", data_to_send)
    for v in viewers:
        emit("get_data",data_to_send, room=v)


def getId():  
    global nextId
    curId = nextId
    nextId += 1
    return curId

@socketio.on('init_client')
def handle_init_client(json):
    print("init client",request.sid)
    join_room(request.sid)
    new_id = getId()
    print("passsing id {}".format(new_id))
    emit("get_id", {'id':new_id}, room = request.sid)
    # send("init",room=request.sid)
    devices.append(request.sid)
    print("devices:",devices)

    # request.emit("message","414123123")


@socketio.on('dc_client')
def handle_dc_client(json):
    print("disconnect client",request.sid)
    leave_room(json['id'])
    del devices[json['id']]
    print("devices:",devices)


if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()


    # Start app
    # app.run(debug=True,port=80)
    print("Server started")
    socketio.run(app,debug=False,port=80)

