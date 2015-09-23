#!/usr/bin/env python

import os
import sqlite3
import logging
from datetime import datetime, date
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Markup, make_response
from flask_debugtoolbar import DebugToolbarExtension

#create app
app = Flask(__name__)

app.config.from_object('config')
app.config.from_envvar('HOUSECHORESETTINGS', silent=True)
app.debug=app.config['DEBUG']
toolbar=DebugToolbarExtension(app)

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
    
    And set up the default admin account.
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

def get_users_role():
    """Get a list of the users and their roles
    """
    db=get_db()
    cursor=db.execute('select * from users')
    rows=cursor.fetchall()
    logging.debug('Getting the users list')
    return rows

def get_roles():
    """Get a list of the roles
    """
    db=get_db()
    cursor=db.execute('select * from roles')
    rows=cursor.fetchall()
    logging.debug('Getting the roles list')
    return rows

def get_userid(name):
    """Get the userid from person with name=name
    """
    try:
        db=get_db()
        cursor = db.execute('select id from persons where name=?',[name])
        row=cursor.fetchone()
        logging.debug('Getting the userid for user: ' + name)
        return row[0]
    except:
        logging.critical('Error with getting userid from database')
        raise

def get_choreid(chore):
    """Get the choreid from chore with name=name
    """
    try:
        db=get_db()
        logging.debug('getting the chore_id for a specific chore: ' + chore)
        cursor = db.execute('select id from chores where name=?',[chore])
        row=cursor.fetchone()
        return row[0]
    except:
        logging.critical('Error with getthing the chore id from the database')
        raise

def check_login(user, password):
    """Check the provided username and password
    """
    db=get_db()
    logging.debug('Checking user and password: ' + user + ', ' + password)
    cur=db.execute('select id from persons where name=? and password=?',[user.lower(), password])
    row=cur.fetchone()
    if row:
        return row[0]
    else:
        return None

def check_admin(userid):
    """Check if current user had admin rights.
    """
    db=get_db()
    cur=db.execute('select role_name from users where person_id=?', [userid])
    row=cur.fetchone()
    logging.debug('Role of current user: ' + row[0])
    return row[0]=='admin'

################################################################################
# APP ADMIN
#
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request.
    """
    if hasattr(g, 'db'):
        logging.debug('closing the database')
        g.db.close()

@app.before_request
def before_request():
    """before processing: check if user is logged in.
    or wants to login
    or is requesting static data
    """
    try:
        path=request.path.split('/')[1]
        extension=request.path.split('/')[-1].split('.')[-1]
    except:
        path=None
        extension=None
    if 'uid' in session:
        g.current_user=session['uid']
        db=get_db()
        cursor=db.execute("select message from meta where key= 'appversion'")
        g.appversion=cursor.fetchone()[0]
        cursor=db.execute("select message from meta where key= 'dbversion'")
        g.dbversion=cursor.fetchone()[0]
        pass
    elif (request.endpoint=='login' or request.endpoint=='loginscreen'):
        pass
    elif (path=='static' and extension in ('js','css')):
        pass
    elif (path=='_debug_toolbar' and extension in ('js', 'css')):
        pass
    else:
        flash("You don't fool me! Login first!","danger")
        logging.warning('False attempt on %s: not logged in.' %(request.path))
        return redirect(url_for('loginscreen'))

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
    return render_template('index.html',is_admin=check_admin(g.current_user), appversion=g.appversion, dbversion=g.dbversion)

@app.route('/initdb')
def initdb():
    """Initialize the database
    """
    logging.info('requesting to initialise the database')
    if check_admin(g.current_user):
        init_the_db()
        flash('Created new database','warning')
    if request.referrer:
        #refresh the referring page
        return redirect(request.referrer)
    else:
        #if not possible: return to index
        return redirect (url_for('index'))

@app.route('/filldbsampledata')
def fill_db_sample_data():
    """fill the database with sample data
    """
    db=get_db()
    if check_admin(g.current_user):
        try:
            with app.open_resource('../sql/insert_sampledata.sql','r') as f:
                logging.warning('inserting sample data in database')
                db.cursor().executescript(f.read())
            db.commit()
            flash('Filled database with sample data','warning')
        except:
            logging.critical('Error with filling the sample database.')
    if request.referrer:
        #refresh the referring page
        return redirect(request.referrer)
    else:
        #if not possible: return to index
        return redirect (url_for('index'))

@app.route('/loginscreen')
def loginscreen():
    """Show the loginscreen

    If there is no databse yet (and thus no way of checking user credentials),
    init the database and create a stand admin account. This should only happen
    on first use.
    """
    if not(os.path.isfile(app.config['DATABASE'])):
        # database doesn't exist yet --> create it
        open(app.config['DATABASE'], 'a').close()
        init_the_db()
        g.current_user=1
        session['uid']=1
        flash('Created default account: user=admin, pass=admin','warning')
        logging.warning('Created a default admin account')
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Check user login

    if valid: redirect to index
    if not valid: return to loginscreen
    """
    if request.form['user'] and request.form['password']:
        pass_login=check_login(request.form['user'], request.form['password'])
        if pass_login:
            logging.info('User %s passed login'%(request.form['user']))
            g.current_user=pass_login
            session['uid']=pass_login
            return redirect(url_for('index'))
    logging.warning('User did NOT pass login')
    flash('Wrong username / password combination', 'danger')
    return redirect(url_for('loginscreen'))

@app.route('/logout')
def logout():
    """Log out
    """
    logging.info('User %s trying to log out' %(g.current_user))
    session.pop('uid')
    g.current_user=None
    flash('You were logged out','info')
    return redirect(url_for('loginscreen'))

@app.route('/export_xml')
def export_xml():
    """Export the database as XML
    """
    if check_admin(g.current_user):
        try:
            db=get_db()
            cur=db.execute('select * from xml_output')
            rows=cur.fetchall()
            writefile=app.config['XMLEXPORT']+'_' + str(g.current_user) + '.xml'
            with open(writefile,'w') as f:
                for row in rows:
                    f.write(row[0] + '\n')
            logging.debug('Fetching the database as xml output.')
            flash(Markup('You can download the xml <a download href="' + url_for('download_xml') + '" target="_blank">file here</a>.'), 'info')
        except:
            logging.critical('Error with exporting as xml')
            raise
    if request.referrer:
        #refresh the referring page
        return redirect(request.referrer)
    else:
        #if not possible: return to index
        return redirect (url_for('index'))

@app.route('/download_xml')
def download_xml():
    """Download the generated xml
    """
    if check_admin(g.current_user):
        writefile=app.config['XMLEXPORT']+'_' + str(g.current_user) + '.xml'
        with open(writefile,'r') as f:
            down=f.read()
        response=make_response(down)
        response.headers["Content-Disposition"] = '"attachment; filename=' + writefile + '"'
        return response
    else:
        if request.referrer:
            #refresh the referring page
            return redirect(request.referrer)
        else:
            #if not possible: return to index
            return redirect (url_for('index'))

#PAGES
@app.route('/overview')
def overview():
    """Generate a simple overview of all the actions
    """
    logging.debug('Generating the overview page')
    db=get_db()
    cursor=db.execute('select * from overview order by action_date desc, chore asc')
    rows=cursor.fetchall()
    rows=[dict(id=-1,action_date=None, person_name=None,chore='No chores yet')] if len(rows)==0 else rows
    today=datetime.today().strftime('%Y-%m-%d')
    return render_template('overview.html', rows=rows, chores=get_chores(), users=get_users(), today=today,is_admin=check_admin(g.current_user), appversion=g.appversion, dbversion=g.dbversion)

@app.route('/chores_lastaction')
def chores_lastaction():
    """Generate a simple overview of all the chores with their last actioned
    date.
    """
    logging.debug('Generating the chores_lastaction page')
    db=get_db()
    cursor=db.execute('select * from chores_lastaction')
    rows=cursor.fetchall()
    return render_template('chores_lastaction.html', rows=rows,is_admin=check_admin(g.current_user), appversion=g.appversion, dbversion=g.dbversion)

@app.route('/user_admin')
def user_admin():
    """Render the user and role admin page
    """
    if check_admin(g.current_user):
        logging.debug('Generating the user admin page')
        if check_admin(g.current_user):
            users=get_users_role();
            roles=get_roles()
            return render_template('user_admin.html', users=users, roles=roles,is_admin=check_admin(g.current_user), appversion=g.appversion, dbversion=g.dbversion)
    return redirect (url_for('index'))

#ACTIONS
@app.route('/new_action', methods=['POST'])
def new_action():
    """Get the URL request with the data for a newly performed action

    TODO: check SQL-injection
    TODO: validate dataentry
    """
    try:
        db=get_db()
        db.execute('insert into actions (action_date, person_id, chore_id) values (?, ?, ?)',
            [request.form['date'], request.form['person'], request.form['chore']])
        db.commit()
        flash('New action added', 'success')
        logging.info('New action added')
        return redirect(url_for('overview'))
    except:
        logging.critical('Error with inserting new action.')
        raise

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

    TODO: check SQL injection
    TODO: validate dataentry
    """
    try:
        db=get_db()
        choreid=get_choreid(request.form['chore'])
        personid=get_userid(request.form['person'])
        db.execute('update actions set chore_id=?, action_date=?, person_id=? where id=?',[choreid,request.form['date'],personid, request.form['id']])
        db.commit()
        flash('Updated action','success')
        logging.info('Updated action with id=%s' %(request.form['id']))
        return redirect(url_for('overview'))
    except:
        logging.critical('Error with updating action.')
        raise

@app.route('/copy_to_today/<id>')
def copy_to_today(id):
    """copy the action with action_id=<id> to today
    """
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
    today=str(date.today().strftime('%Y-%m-%d'))
    db=get_db()
    db.execute('insert into actions (action_date, person_id, chore_id) values(?,?,?)', [today, g.current_user, id])
    db.commit()
    flash('Chore added to today','success')
    logging.info('Action added')
    return redirect( url_for('chores_lastaction'))

@app.route('/delete_chore/<id>')
def delete_chore(id=0):
    """Delete chore with id=id
    """
    if check_admin(g.current_user):
        db=get_db()
        db.execute('delete from chores where id = ?',[id])
        db.commit()
        db.execute('delete from actions where chore_id = ?',[id])
        db.commit()
        flash('Chore removed', 'info')
        logging.info('Removed chore with id=%s' %id)
    return redirect( url_for('chores_lastaction'))

@app.route('/new_chore', methods=['POST'])
def new_chore():
    """Get the URL request with data for a new chore

    TODO: check SQL-injection
    TODO: validate dataentry
    """
    try:
        if check_admin(g.current_user):
            db=get_db()
            db.execute('insert into chores (name) values (?)',[request.form['chore']])
            db.commit()
            flash('New chore added', 'success')
            logging.info('New chore added: %s' %(request.form['chore']))
        return redirect(url_for('chores_lastaction'))
    except:
        logging.critical('Error with adding new chore.')
        raise

@app.route('/edit_chore',methods=['POST'])
def edit_chore():
    """Edit a chore

    The POST data should contain the chore_id and the new chore description

    TODO: check SQL injection
    TODO: validate dataentry
    """
    try:
        if check_admin(g.current_user):
            db=get_db()
            db.execute('update chores set name = ? where id = ?',[request.form['chore'], request.form['id']])
            db.commit()
            flash('Chore updated', 'success')
            logging.info('Edited chore with id=%s to %s' %(request.form['id'], request.form['chore']))
        return redirect(url_for('chores_lastaction'))
    except:
        logging.critical('Error with updating chore.')
        raise

#USERS
@app.route('/new_user', methods=['POST'])
def new_user():
    """Get the URL request with data for a new user

    TODO: check SQL-injection
    TODO: validate dataentry
    """
    try:
        if check_admin(g.current_user):
            db=get_db()
            db.execute('insert into persons (name, password, role_id) values (?,?,?)',[request.form['name'], 'resu', request.form['roles']])
            db.commit()
            flash('New user added, password: resu', 'success')
            flash('Please change the password','danger')
            logging.info('New user added: %s' %(request.form['name']))
            return redirect(url_for('user_admin'))
        else:
            return redirect(url_for('index'))
    except:
        logging.critical('Error with adding new user.')
        raise

@app.route('/delete_user/<id>')
def delete_user(id):
    """Delete user with id=id
    """
    if check_admin(g.current_user):
        db=get_db()
        db.execute('delete from persons where id = ?',[id])
        db.commit()
        flash('User removed', 'info')
        logging.info('Removed user with id=%s' %id)
        return redirect( url_for('user_admin'))
    else:
        return redirect(url_for('index'))

@app.route('/edit_user', methods=['POST'])
def edit_user():
    """Edit a user

    The POST data should contain the user_id and the new user

    TODO: check SQL injection
    TODO: validate dataentry
    """
    try:
        if check_admin(g.current_user):
            db=get_db()
            if request.form['passw'] and len(request.form['passw'])>3:
                # checking if password is filled in
                db.execute('update persons set name = ?, password= ? , role_id= ? where id = ?',[request.form['person'], request.form['passw'], request.form['role'], request.form['id']])
            else:
                db.execute('update persons set name = ?, role_id= ? where id = ?',[request.form['person'], request.form['role'], request.form['id']])
            db.commit()
            flash('User updated', 'success')
            logging.info('Edited user with id=%s' %(request.form['id']))
            return redirect(url_for('user_admin'))
        else:
            return redirect(url_for('index'))
    except:
        logging.critical('Error with editing new user.')
        raise

################################################################################
# RUN
#
if __name__=='__main__':
    logging.critical('FIRING UP THE FLASK APPLICATION')
    app.run(host='0.0.0.0')
