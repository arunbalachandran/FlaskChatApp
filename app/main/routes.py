from flask import session, redirect, url_for, render_template, request, escape
from . import main
from .forms import LoginForm, SignupForm, ConnectToForm
import json
from flask_socketio import emit, join_room, close_room
from .. import socketio
import sys

user_id_dict = {}
available_users = []
connection_dict = {}

# get method by default
@main.route('/', methods=['GET'])
def showoptions():
    '''Show the list of actions that a user can perform.
       The function names act as unique identifiers for redirection.'''
    return render_template('index.html')


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    '''Sign up functionality'''
    form = SignupForm()
    # check if the credentials do not already exist
    if request.method == 'POST' and form.validate():
        user = form.username.data
        password = form.password.data
        # worst method of storing usernames and passwords
        # check if username already exists
        with open('userdb.txt', 'r') as fp:
            userlist =  [i.split(',')[0] for i in fp.readlines()]
            # how to stop auto submit?
            if user in userlist:
                return json.dumps({'error': 'User already exists'}), 409, {'ContentType': 'application/json'}
        with open('userdb.txt', 'a') as fp:
            fp.write(user + ',' + password + '\n')
            return json.dumps({'success': 'User created successfully'}), 200, {'ContentType': 'application/json'}
    return render_template('signup.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    """"Login form to enter a room."""
    form = LoginForm()
    # check the validity of credentials
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # who_to_talk_to = form.connectto.data
        with open('userdb.txt') as fp:
            data_values = fp.read()
            data_values = data_values.split()
            data_values = [i.split(',') for i in data_values]
            for data in data_values:
                # list of users online updated in session
                if username == data[0] and password == data[1]:
                    return json.dumps({'success': username}), 200, {'ContentType': 'application/json'}
            return json.dumps({'error': 'User not found'}), 409, {'ContentType': 'application/json'}
    return render_template('login.html', form=form)

@main.route('/loggedin', methods=['GET', 'POST'])
def showloginpage():
    '''Logged in and ready to connect to other users'''
    form = ConnectToForm()
    global user_id_dict, available_users
    # on getting get request from login page
    if request.method == 'GET':
        sock_user = request.args.get('sock_user')
        user = sock_user
        if user not in available_users:
            available_users.append(user)
        # at this point we dont have sock user id
        return render_template('loggedin.html', name=user, form=form)
    elif request.method == 'POST':
        # data should be in fomr now due to post callout
        # get the socket id that can uniquely identify users
        identity = request.json['sock_id']
        user = request.json['username']
        # map user to his/her socket
        user_id_dict[user] = identity
        # connect to my own room
        room = identity
        # sock_user_id = user + ' ' + identity
        # sys.stderr.write('sending out socket user id '+str(sock_user_id))
        return json.dumps({'success': user, 'room': room}), 200, {'ContentType': 'application/json'}


@main.route('/checkcred', methods=['POST'])
def checkcred():
    '''check cred'''
    global connection_dict
    if request.method == 'POST':
        # is this order dependent?
        connect_to = request.json[1]['value']
        # sock_id = request.json[2]['sock_id']
        user = request.json[2]["username"]
        # the user you want to connect to doesn't exist'
        # if there is an error
        if (connect_to in available_users):
            # join_room(connect_to)
            connect_id = user_id_dict[connect_to]
            # user = [i for i in user_id_dict if user_id_dict[i] == sock_id][0]
            # user in connection dict is connected to connect_to
            connection_dict[user] = connect_to
            connection_dict[connect_to] = user
            return json.dumps({'success': user, 'room': connect_id}), 200, {'ContentType': 'application/json'}
            # if ()
            # connect_id = user_id_dict[connect_to]
            # if (user < connection_dict[user]):
            #     sys.stderr.write('Connected to room ' + user + ' ' + connect_to + '\n')
                # return json.dumps({'success': user + '_' + connect_to + '_0', 'connect_id': connect_id}), 200, {'ContentType': 'application/json'}
            # else:
            #     sys.stderr.write('Connected to room ' + connect_to + '_' + user + '\n')
            #     return json.dumps({'success': connect_to + '_' + user + '_1', 'connect_id': connect_id}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'error': 'User is not connected in room '}), 409, {'ContentType': 'application/json'}


@main.route('/logout', methods=['GET', 'POST'])
def loggedout():
    '''Logged in and ready to connect to other users'''
    return redirect(url_for('.showoptions'))


@socketio.on('joined', namespace='/loggedin')
def joined(message):  # get myId as input
    """Sent by other? clients when they enter a room.
    A status message is broadcast to all people in the room."""
    user, room = message['user'], message['room']
    sys.stderr.write('\nUser ' + user + ' is getting connnected to ' + room)
    join_room(room)
    # now make other user join the room
    emit('status', {'mesg': user + ' has entered the room -> ' + room}, room=room)


@socketio.on('text', namespace='/loggedin')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    user = message['sock_user']
    # self_room = user
    room = connection_dict.get(user, user)
    sys.stderr.write('\nText to write is ' + message['text'] + ' to room ' + room)
    # sys.stderr.write('\nChanges here in' + room)
    # print message here
    emit('status', {'mesg': message['text']}, room=room)
    # emit('message', {'msg': message['text']}, room=room)
    sys.stderr.write('\nFinished writing text!')


@socketio.on('left', namespace='/loggedin')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    user = message['username']
    # get the room or empty string if none exists
    room = message['sock_id']
    close_room(room)
    emit('status', {'msg': user + ' has left the room.'}, room=room)
