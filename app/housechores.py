import os
import sqlite3
import logging
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

#create app
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'chores.db'),
    DEBUG=True,
    SECRET_KEY='thisisareallysecretkeydon7you71nk',
    USERNAME='admin',
    PASSWORD='admin',
    LOGFILE = 'log.log',
    LOGFILEMODE = 'w',
    LOGFORMAT = '%(asctime)s - %(funcName)s from %(filename)s, line: %(lineno)s - %(levelname)s: %(message)s',
    LOGLEVEL = 'DEBUG'
))

app.config.from_envvar('HOUSECHORESETTINGS', silent=True)

# SETUP LOGGING
logging.basicConfig(
    filename=app.config['LOGFILE'],
    filemode=app.config['LOGFILEMODE'],
    format=app.config['LOGFORMAT'],
    level=app.config['LOGLEVEL']
)

def get_db():
    """Connects to the database
    """
    if not hasattr(g, 'db'):
        g.db= sqlite3.connect(app.config['DATABASE'])
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request.
    """
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/')
def index():
    logging.debug('returning index')
    return render_template('index.html')

@app.route('/initdb')
def initdb():
    """Initialize the database

    TODO: only when admin
    """
    db=get_db()
    with app.open_resource('../sql/create_tables.sql','r') as f:
        logging.warning('performing initdb: create_tables.sql')
        db.cursor().executescript(f.read())
    db.commit()
    flash('Created new database','warning')
    return redirect(url_for('index'))

@app.route('/filldbsampledata')
def fill_db_sample_data():
    """fill the database with sample data

    TODO: only when admin
    TODO: check if database exists and tables ares present
    """
    db=get_db()
    with app.open_resource('../sql/insert_sampledata.sql','r') as f:
        logging.warning('inserting sample data in database')
        db.cursor().executescript(f.read())
    db.commit()
    flash('Filled database with sample data','warning')
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run(host='0.0.0.0')
