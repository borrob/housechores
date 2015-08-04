#!/usr/bin/env python

import os
import sqlite3
import logging
from datetime import date
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
        g.db.row_factory=sqlite3.Row #using row_factory to obtain column_names when we ask for data
        logging.debug('Getting database: ' + app.config['DATABASE'])
    return g.db

def get_chores():
    """Get a list of the current chores
    """
    db=get_db()
    cursor=db.execute('select *from chores')
    rows=cursor.fetchall()
    logging.debug('Getting the chores list')
    return rows

def get_users():
    """Get a list of the current users
    """
    db=get_db()
    cursor=db.execute('select * from persons')
    rows=cursor.fetchall()
    logging.debug('Getting the persons list')
    return rows

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

@app.route('/overview')
def overview():
    """Generate a simple overview of all the actions
    """
    db=get_db()
    cursor=db.execute('select * from overview order by action_date desc, chore asc')
    rows=cursor.fetchall()
    today=date.today().strftime('%Y-%m-%d')
    return render_template('overview.html', rows=rows, chores=get_chores(), users=get_users(),today=today)

@app.route('/chores_lastaction')
def chores_lastaction():
    """Generate a simple overview of all the chores with their last actioned
    date.
    """
    db=get_db()
    cursor=db.execute('select * from chores_lastaction')
    rows=cursor.fetchall()
    return render_template('chores_lastaction.html', rows=rows)

@app.route('/new_action', methods=['POST'])
def new_action():
    """Get the URL request with the data for a newly performed action

    TODO: check loging
    TODO: check if database and schemas exist
    TODO: check SQL-injection
    TODO: validate dataentry
    TODO: add try/catch
    """
    db=get_db()
    db.execute('insert into actions (action_date, person_id, chore_id) values (?, ?, ?)',
        [request.form['date'], request.form['person'], request.form['chore']])
    db.commit()
    flash('New action added', 'success')
    logging.info('New action added')
    return redirect(url_for('overview'))

@app.route('/delete_action/<id>')
def delete_action(id):
    """Delete the action with id = <id>
    """
    db=get_db()
    db.execute('delete from actions where id = ?',[id])
    db.commit()
    flash('Action removed','success')
    logging.info('Action %s removed' %(id))
    return redirect(url_for('overview'))

@app.route('/copy_to_today/<id>')
def copy_to_today(id):
    """copy the action with action_id=<id> to today
    """
    g.current_user=1 #TODO: user real g.current_user
    db=get_db()
    cursor=db.execute('select * from actions where id = ?', [id])
    row=cursor.fetchone()
    chore=row['chore_id']
    today=str(date.today().strftime('%Y-%m-%d'))
    db.execute('insert into actions (action_date,person_id,chore_id) values (?,?,?)' ,[today, g.current_user, chore])
    db.commit()
    flash('Action copied to today','success')
    logging.info('Action with id %s copied to today' %id)
    return redirect(url_for('overview'))

@app.route('/new_from_chore/<id>')
def new_from_chore(id):
    """Inser new action for today of chore with id=<id>
    """
    g.current_user=1 #TODO: real current_user
    today=str(date.today().strftime('%Y-%m-%d'))
    db=get_db()
    db.execute('insert into actions (action_date, person_id, chore_id) values(?,?,?)', [today, g.current_user, id])
    db.commit()
    flash('Chore added to today','success')
    logging.info('Action added')
    return redirect( url_for('chores_lastaction'))
    

if __name__=='__main__':
    app.run(host='0.0.0.0')
