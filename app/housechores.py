#!/usr/bin/env python

import os
import sqlite3
import logging
from datetime import datetime, date
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

def init_the_db():
    """Initialise the database
    """
    db=get_db()
    with app.open_resource('../sql/create_tables.sql','r') as f:
        logging.warning('performing initdb: create_tables.sql')
        db.cursor().executescript(f.read())
    db.commit()

def get_chores():
    """Get a list of the current chores
    """
    db=get_db()
    cursor=db.execute('select *from chores where id>=0')
    rows=cursor.fetchall()
    logging.debug('Getting the chores list')
    return rows

def get_users():
    """Get a list of the current users
    """
    db=get_db()
    cursor=db.execute('select * from persons where id>=0')
    rows=cursor.fetchall()
    logging.debug('Getting the persons list')
    return rows

def get_userid(name):
    """Get the userid from person with name=name

    TODO: check if database and schema exist
    """
    db=get_db()
    cursor = db.execute('select id from persons where name=?',[name])
    row=cursor.fetchone()
    return row[0]

def get_choreid(chore):
    """Get the choreid from chore with name=name

    TODO: check if database and schema exist
    """
    db=get_db()
    cursor = db.execute('select id from chores where name=?',[chore])
    row=cursor.fetchone()
    return row[0]

################################################################################
# APP ADMIN
#
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request.
    """
    if hasattr(g, 'db'):
        g.db.close()

@app.template_filter()
def dayssince(value, the_format='%Y-%m-%d'):
        today=datetime.today()
        if value==None:
            return None
        else:
            the_day= datetime.strptime(value,the_format)
            return (today-the_day).days

app.jinja_env.filters['dayssince'] = dayssince

################################################################################
# APP ROUTES
#
@app.route('/')
def index():
    logging.debug('returning index')
    return render_template('index.html')

@app.route('/initdb')
def initdb():
    """Initialize the database

    TODO: only when admin
    """
    init_the_db()
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

#PAGES
@app.route('/overview')
def overview():
    """Generate a simple overview of all the actions
    """
    db=get_db()
    cursor=db.execute('select * from overview order by action_date desc, chore asc')
    rows=cursor.fetchall()
    rows=[dict(id=-1,action_date=None, person_name=None,chore='No chores yet')] if len(rows)==0 else rows
    today=datetime.today().strftime('%Y-%m-%d')
    return render_template('overview.html', rows=rows, chores=get_chores(), users=get_users(), today=today)

@app.route('/chores_lastaction')
def chores_lastaction():
    """Generate a simple overview of all the chores with their last actioned
    date.
    """
    db=get_db()
    cursor=db.execute('select * from chores_lastaction')
    rows=cursor.fetchall()
    return render_template('chores_lastaction.html', rows=rows)

#ACTIONS
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

@app.route('/edit_action', methods=['POST'])
def edit_action():
    """Edit the action from the post request

    The POST data should contain the action_id and the new chore description
    TODO: check login
    TODO: check if database and schemas exist
    TODO: check SQL injection
    TODO: validate dataentry
    TODO: add try/catch
    """
    db=get_db()
    choreid=get_choreid(request.form['chore'])
    personid=get_userid(request.form['person'])
    db.execute('update actions set chore_id=?, action_date=?, person_id=? where id=?',[choreid,request.form['date'],personid, request.form['id']])
    db.commit()
    flash('Updated action','success')
    logging.info('Updated action with id=%s' %(request.form['id']))
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

#CHORES
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

@app.route('/delete_chore/<id>')
def delete_chore(id):
    """Delete chore with id=id

    TODO: only for admin
    """
    db=get_db()
    db.execute('delete from chores where id = ?',[id])
    db.commit()
    flash('Chore removed')
    logging.info('Removed chore with id=%s' %id)
    return redirect( url_for('chores_lastaction'))

@app.route('/new_chore', methods=['POST'])
def new_chore():
    """Get the URL request with data for a new chore
    TODO: check loging
    TODO: check if database and schemas exist
    TODO: check SQL-injection
    TODO: validate dataentry
    TODO: add try/catch
    """
    db=get_db()
    db.execute('insert into chores (name) values (?)',[request.form['chore']])
    db.commit()
    flash('New chore added')
    logging.info('New chore added: %s' %(request.form['chore']))
    return redirect(url_for('chores_lastaction'))

@app.route('/edit_chore',methods=['POST'])
def edit_chore():
    """Edit a chore

    The POST data should contain the chore_id and the new chore description
    TODO: check login
    TODO: check if database and schemas exist
    TODO: check SQL injection
    TODO: validate dataentry
    TODO: add try/catch
    """
    db=get_db()
    db.execute('update chores set name = ? where id = ?',[request.form['chore'], request.form['id']])
    db.commit()
    flash('Chore updated', 'success')
    logging.info('Edited chore with id=%s to %s' %(request.form['id'], request.form['chore']))
    return redirect(url_for('chores_lastaction'))

################################################################################
# RUN
#
if __name__=='__main__':
    app.run(host='0.0.0.0')
