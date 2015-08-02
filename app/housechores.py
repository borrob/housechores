import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

#create app
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'chores.db'),
    DEBUG=True,
    SECRET_KEY='thisisareallysecretkeydon7you71nk',
    USERNAME='admin',
    PASSWORD='admin'
))

#app.config.from_envvar('HOUSECHORESETTINGS', silent=True)

@app.route('/')
def index():
    return render_template('index.html')

if __name__=='__main__':
    app.run(host='0.0.0.0')
