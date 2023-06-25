#!/usr/bin/env python3
# encoding: utf8
'''
A very simple Flask based web server with user logins, based on many examples
floating around the on the web
'''

from datetime import datetime
from logging import basicConfig, getLogger
import os
# from socket import gethostname
import sys
from threading import Thread, Event, current_thread

from flask import Flask, request, session, url_for, flash, get_flashed_messages
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, \
    login_user, logout_user, login_required, current_user
from jinja2 import Template
from werkzeug.serving import make_server
from werkzeug.urls import url_parse
from werkzeug.utils import redirect

from sbci import to_bool, popattr


# default app configuration - imported by app.config.from_object() call below
DEBUG = to_bool(os.environ.get('DEBUG', 'True'))
SECRET_KEY = os.environ.get('SECRET_KEY', '39b4133d572ca172dc97f42f10d7b514')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8088'))
# SSL_DIR = os.environ.get('SSL_DIR', 'ssl')
# SSL_CERT = os.environ.get(
#     'SSL_CERT', os.path.join(SSL_DIR, 'certs', gethostname() + '.pem')
# )
# SSL_KEY = os.environ.get(
#     'SSL_KEY', os.path.join(SSL_DIR, 'private', gethostname() + '.pem')
# )


basicConfig(level='DEBUG' if DEBUG else 'INFO')


app = Flask(__name__)
app.config.from_object(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
app.logger = getLogger(__name__)


# Flask-Login tutorial here:
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


flask_app_css_template = Template('''\
.loginitem {
  display: flex;
  justify-content: space-between;
  margin: 10px auto;
  min-width: 100px;
}

.loginbox {
  border: 1px solid black;
  border-radius: 5px;
  width: 250px;
  margin: auto;
  padding: 0px 10px;
}

.loginerrs {
  margin: auto;
  color: red;
}

.header {
  display: flex;
  width: 100%;
}

.expand {
  flex-grow: 100;
}
''')


@app.route('/flask_app.css')
def flask_app_css():
    response = app.make_response(flask_app_css_template.render())
    response.mimetype = 'text/css'
    response.cache_control.max_age = 0
    return response


flask_app_header = '''\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <link rel="stylesheet" type=text/css href="{{ flask_app_css_url }}">
    <title>{{ page_title }}</title>
  </head>
  <body>
    <div class="header">
      <a href="{{ index_url }}">Home</a>
      <div class="expand"></div>
      {% if session['username'] %}
        Logged in as {{ session['username'] }}
      {% else %}
        Not logged in!
      {% endif %}
      &nbsp;
      {% if current_user.is_anonymous %}
      <a href="{{ login_url }}">Login</a>
      {% else %}
      <a href="{{ logout_url }}">Logout</a>
      {% endif %}
    </div>
'''


flask_app_footer = '''\
  </body>
</html>
'''


index_template = Template(flask_app_header + flask_app_footer)


@app.route('/')
@app.route('/index')
@login_required
def index():
    response = app.make_response(
        index_template.render(
            page_title='Page Title Goes Here!',
            flask_app_css_url=url_for('flask_app_css'),
            index_url=url_for('index'),
            login_url=url_for('login'),
            logout_url=url_for('logout'),
            session=session,
            current_user=current_user,
        )
    )
    response.mimetype = 'text/html'
    response.cache_control.max_age = 0
    return response


@app.route('/teams')
def teams():
    raise NotImplementedError


@app.route('/shutdown')
@login_required
def shutdown():
    flask_thread = popattr(app, '_flask_thread', None)
    if flask_thread is not None:
        flask_thread.terminate.set()
        return 'server shutdown signal sent!'
    else:
        return 'huh? server should already be shutdown!'


class User(UserMixin):
    '''just holds PAM username - enhance with PAM session and account info?'''

    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    def __str__(self):
        return self.username


login_template = Template(flask_app_header + '''\
    <form action="" method="POST">
      <div class="loginbox">
        <div class="loginerrs">{{ flashed_messages }}</div>
        <div class="loginitem">
          <label for="username">Username:</label>
          <input type="text" name="username" id="username">
        </div>
        <div class="loginitem">
          <label for="password">Password:</label>
          <input type="password" name="password" id="password">
        </div>
        <input class="loginitem" type="submit" value="Login">
      </div>
    </form>
''' + flask_app_footer)

# PAM authentication based on example for "simplepam" here:
# https://stackoverflow.com/a/26319744/2130789


try:
    from pam import authenticate
except ImportError:
    app.logger.error('PAM authentication unavailable - install python3-pampy')

    def authenticate(_username, _password):
        '''PAM module not available'''
        return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password) or (
            username == 'guest' and password == 'guest'
        ):
            session['username'] = username
            login_user(User(username))
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        else:
            app.logger.error('Auth failed: username={}'.format(username))
            flash('Invalid username or password')
            return redirect(url_for('login'))
    else:
        flashed_messages = ''
        for flashed_message in get_flashed_messages():
            if len(flashed_messages) > 0:
                flashed_messages += '<br>'
            flashed_messages += flashed_message
        response = app.make_response(
            login_template.render(
                page_title='Login Id',
                flashed_messages=flashed_messages,
                flask_app_css_url=url_for('flask_app_css'),
                index_url=url_for('index'),
                login_url=url_for('login'),
                logout_url=url_for('logout'),
                session=session,
                current_user=current_user,
            )
        )
        response.mimetype = 'text/html'
        response.cache_control.max_age = 0
        return response


@login_manager.user_loader
def load_user(username):
    return User(username) if username == session['username'] else None


@app.route('/logout')
def logout():
    logout_user()
    # remove the username from the session if it's there
    _ = session.pop('username', None)
    return redirect(url_for('index'))


class FlaskThread(Thread):
    '''https://stackoverflow.com/a/45017691/2130789'''

    def __init__(self):
        super(FlaskThread, self).__init__(name=__name__)

        self.logger = getLogger(self.__class__.__name__)

        self.started = Event()
        self.terminate = Event()
        self.finished = Event()

        self.host = app.config['HOST']
        self.port = int(app.config['PORT'])
        self.logger.info('server: host=%s, port=%d.', self.host, self.port)

        # use of ssl_context explained here:
        # https://stackoverflow.com/a/42906465/2130789
        self.server = make_server(self.host, self.port, app,
                                  # ssl_context=(SSL_CERT, SSL_KEY)
                                  )
        self.ctx = app.app_context()
        self.ctx.push()

        app._flask_thread = self

    def run(self):
        self.logger.info('server: starting ...')
        self.started.set()
        try:
            self.server.serve_forever()
        except Exception:
            self.logger.exception('server: exception in serve_forever()!')
        self.finished.set()
        self.logger.info('server: finished.')

    def shutdown(self):
        self.logger.info('server: shutting down ...')
        if current_thread() is self:
            raise RuntimeError('cannot call shutdown from server thread!')
        if not self.started.is_set():
            raise RuntimeError('shutdown called before server has started!')
        if self.finished.is_set():
            raise RuntimeError('shutdown called after server has terminated!')
        self.server.shutdown()


def main():

    app.logger.info('App started at %s.', datetime.now().isoformat(' '))

    # if not os.access(SSL_CERT, os.R_OK):
    #     app.logger.error('cannot read ssl cert file ({})'.format(SSL_CERT))
    #     return os.EX_OSFILE

    # if not os.access(SSL_KEY, os.R_OK):
    #     app.logger.error('cannot read ssl key file ({})'.format(SSL_KEY))
    #     return os.EX_OSFILE

    flask_thread = FlaskThread()
    flask_thread.daemon = True
    flask_thread.start()

    try:
        flask_thread.terminate.wait()
    except KeyboardInterrupt:
        app.logger.info('App received keyboard inetrrupt - exiting ...')

    flask_thread.shutdown()
    flask_thread.join(5.0)
    if flask_thread.is_alive():
        app.logger.error('timed-out waiting for server thread to finish!')

    app.logger.info('App normal exit at %s.', datetime.now().isoformat(' '))

    return os.EX_OK


if __name__ == '__main__':
    sys.exit(main())
