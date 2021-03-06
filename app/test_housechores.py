#!/usr/bin/env python
"""
Unit tests for housechores
Based on pytest

Run via (auto discover will recognize this file_):
>>>> py.test
"""
import os
import pytest
import tempfile

import housechores

@pytest.fixture
def client(request):
    db_fd, housechores.app.config['DATABASE'] = tempfile.mkstemp()
    housechores.app.config['TESTING'] = True
    housechores.app.config['SERVER_NAME']='localhost:5000'
    housechores.app.config['SECRET_KEY']='testingkey'
    housechores.app.config['DEBUG']=False
    client = housechores.app.test_client()
    with housechores.app.app_context():
        housechores.init_the_db()
    
    def teardown():
        os.close(db_fd)
        os.unlink(housechores.app.config['DATABASE'])
    request.addfinalizer(teardown)

    return client

def login(client, user='admin', password='admin'):
    """perform a basic login
    """
    return client.post('/login', data=dict(user=user, password=password), follow_redirects=True)

def sample_db(client):
    """Fill the database with sample data
    """
    client.get('/filldbsampledata',follow_redirects=True)

def test_Root(client):
    """Test if the application is running
    """
    login(client)
    rv=client.get('/')
    assert b'Welcome to the house chores' in rv.data

def test_empty_overviewpage(client):
    """Test: with an empty database, the overview page is blank
    The page should return 'No chores yet'
    """
    login(client)
    rv=client.get('/overview')
    assert b'No chores yet' in rv.data

def test_sample_data_loaded(client):
    """Test: After loading the sample data, the overview page
    should return something about 'dishes'
    """
    login(client)
    sample_db(client)
    rv=client.get('/overview')
    assert b'<td>dishes</td>' in rv.data

### Actions test
def test_remove_action(client):
    """Test deleting an action
    """
    login(client)
    sample_db(client)
    #test if 'change bedsheets' is present to start with
    rv=client.get('/overview')
    assert b'<td>change bedsheets</td>' in rv.data
    #remove bedsheets
    rv=client.get('/delete_action/5', follow_redirects=True)
    assert b'Action removed' in rv.data #check if message for 'delete successful' is returned
    assert b'<td>change bedsheets</td>' not in rv.data #check if items really is deleted

def test_remove_action_non_admin(client):
    """Test deleting an action as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    #test if 'change bedsheets' is present to start with
    rv=client.get('/overview')
    assert b'<td>change bedsheets</td>' in rv.data
    #remove bedsheets
    rv=client.get('/delete_action/5', follow_redirects=True)
    assert b'Action removed' in rv.data #check if message for 'delete successful' is returned
    assert b'<td>change bedsheets</td>' not in rv.data #check if items really is deleted

def test_add_action(client):
    """Test adding a new action
    """
    login(client)
    sample_db(client)
    #test null-hypothesis
    rv=client.get('/overview')
    assert b'<td>groceries lidl</td>' not in rv.data
    #add new action
    rv=client.post('/new_action', data=dict(date='20-10-2015', person=1, chore=4),follow_redirects=True)
    #test flash message and check item is added
    assert b'New action added' in rv.data
    assert b'<td>groceries lidl</td>' in rv.data

def test_add_action_non_admin(client):
    """Test adding a new action as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    #test null-hypothesis
    rv=client.get('/overview')
    assert b'<td>groceries lidl</td>' not in rv.data
    #add new action
    rv=client.post('/new_action', data=dict(date='20-10-2015', person=1, chore=4),follow_redirects=True)
    #test flash message and check item is added
    assert b'New action added' in rv.data
    assert b'<td>groceries lidl</td>' in rv.data

def test_edit_action(client):
    """Test edit action
    """
    login(client)
    sample_db(client)
    rv=client.get('/overview')
    assert b'<td>1980-01-01</td>' not in rv.data
    assert b'<td>groceries lidl</td>' not in rv.data
    assert b'<td>random</td>' not in rv.data
    #edit action
    rv=client.post('/edit_action', data=dict(id=1,chore='groceries lidl',person='random', date='1980-01-01'), follow_redirects=True)
    assert b'Updated action' in rv.data
    assert b'<td>1980-01-01</td>' in rv.data
    assert b'<td>groceries lidl</td>' in rv.data
    assert b'<td>random</td>' in rv.data

def test_edit_action_non_admin(client):
    """Test edit action as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/overview')
    assert b'<td>1980-01-01</td>' not in rv.data
    assert b'<td>groceries lidl</td>' not in rv.data
    assert b'<td>random</td>' not in rv.data
    #edit action
    rv=client.post('/edit_action', data=dict(id=1,chore='groceries lidl',person='random', date='1980-01-01'), follow_redirects=True)
    assert b'Updated action' in rv.data
    assert b'<td>1980-01-01</td>' in rv.data
    assert b'<td>groceries lidl</td>' in rv.data
    assert b'<td>random</td>' in rv.data

### Chores test
def test_remove_chore(client):
    """Test to remove an existing chore
    """
    login(client)
    sample_db(client)
    rv=client.get('/chores_lastaction')
    assert b'<td>dishes</td>' in rv.data
    rv=client.get('/delete_chore/1', follow_redirects=True)
    assert b'Chore removed' in rv.data
    assert b'<td>dishes</td>' not in rv.data

def test_remove_chore_non_admin(client):
    """Test to remove an existing chore as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/chores_lastaction')
    assert b'<td>dishes</td>' in rv.data
    rv=client.get('/delete_chore/1', follow_redirects=True)
    assert b'Chore removed' not in rv.data
    assert b'<td>dishes</td>' in rv.data

def test_add_chore(client):
    """Test adding a chore
    """
    login(client)
    rv=client.post('/new_chore', data=dict(chore='thisisanewchore'),follow_redirects=True)
    assert b'New chore added' in rv.data #test the flash message
    assert b'<td>thisisanewchore</td>' in rv.data #test the actual insert

def test_add_chore_non_admin(client):
    """Test adding a chore as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.post('/new_chore', data=dict(chore='thisisanewchore'),follow_redirects=True)
    assert b'New chore added' not in rv.data #test the flash message
    assert b'<td>thisisanewchore</td>' not in rv.data #test the actual insert

def test_edit_chore(client):
    """Test edit chore
    """
    login(client)
    sample_db(client)
    rv=client.get('/chores_lastaction')
    assert b'<td>close curtains</td>' not in rv.data
    #edit action
    rv=client.post('/edit_chore', data=dict(id=5,chore='close curtains'), follow_redirects=True)
    assert b'Chore updated' in rv.data
    assert b'<td>close curtains</td>' in rv.data

def test_edit_chore_non_admin(client):
    """Test edit chore as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/chores_lastaction')
    assert b'<td>close curtains</td>' not in rv.data
    #edit action
    rv=client.post('/edit_chore', data=dict(id=5,chore='close curtains'), follow_redirects=True)
    assert b'Chore updated' not in rv.data
    assert b'<td>close curtains</td>' not in rv.data

### login
def test_login_required(client):
    """not login in should get you nowhere
    """
    rv=client.get('/', follow_redirects=True)
    assert b'Login first!' in rv.data
    assert b'Welcome to the house chores' not in rv.data
    login(client)
    rv=client.get('/', follow_redirects=True)
    assert b'Login first!' not in rv.data
    assert b'Welcome to the house chores' in rv.data

def test_nologin_for_static(client):
    """Javascript and css should be available without login
    """
    rv=client.get('/static/jquery-2.1.4.min.js', follow_redirects=True)
    assert b'jQuery' in rv.data
    assert b'Login first!' not in rv.data
    login(client)
    rv=client.get('/static/jquery-2.1.4.min.js', follow_redirects=True)
    assert b'jQuery' in rv.data
    assert b'Login first!' not in rv.data
    rv=client.get('/static/override.css', follow_redirects=True)
    assert b'body {' in rv.data
    assert b'Login first!' not in rv.data
    login(client)
    rv=client.get('/static/override.css', follow_redirects=True)
    assert b'body {' in rv.data
    assert b'Login first!' not in rv.data

def test_login1(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client)
    assert b'Welcome to the house chores' in rv.data
    assert b'Wrong username / password combination' not in rv.data

def test_login2(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, user='wronguser')
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_login3(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, password='wrongpassword')
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_login4(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, user='wronguser', password='wrongpassword')
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_logout(client):
    """After logout no page should be available anymore
    """
    rv=login(client)
    assert b'Welcome to the house chores' in rv.data
    rv=client.get('/logout', follow_redirects=True)
    assert b'You were logged out' in rv.data
    rv=client.get('/', follow_redirects=True)
    assert b'Welcome to the house chores' not in rv.data
    assert b'Login first' in rv.data

def test_inlog_non_admin(client):
    """Test if the application is running (also as non admin)
    """
    login(client)
    sample_db(client)
    client.get('/logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/')
    assert b'Welcome to the house chores' in rv.data

def test_login_changepass(client):
    """Test correct username and change it
    """
    rv=login(client)
    assert b'Welcome to the house chores' in rv.data
    assert b'Wrong username / password combination' not in rv.data
    rv=client.post('/edit_user', data=dict(person='newname', role=1, id=1, passw='12345678'), follow_redirects=True)
    rv=client.get('/logout', follow_redirects=True)
    rv=login(client)
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data
    rv=login(client, user='newname')
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data
    rv=login(client, user='newname', password='12345678')
    assert b'Welcome to the house chores' in rv.data
    assert b'Wrong username / password combination' not in rv.data

### user admin
def test_useradmin(client):
    """Test the user admin page
    """
    login(client)
    sample_db(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>rob</td>' in rv.data
    assert b'<td>admin</td>' in rv.data
    assert b'<td>rob</td><td>admin</td>' in rv.data.replace('\n','').replace('\t','')

def test_useradmin_non_admin(client):
    """Test the user admin page as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>rob</td>' not in rv.data
    assert b'<td>admin</td>' not in rv.data
    assert b'<td>rob</td><td>admin</td>' not in rv.data.replace('\n','').replace('\t','')

def test_add_user(client):
    """Test adding a new user
    """
    login(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>dude</td><td>user</td>' not in rv.data.replace('\n','').replace('\t','')
    rv=client.post('/new_user', data=dict(name='dude', roles=2), follow_redirects=True)
    assert b'New user added' in rv.data
    assert b'<td>dude</td><td>user</td>' in rv.data.replace('\n','').replace('\t','')
    rv=client.get('/logout', follow_redirects=True)
    rv=login(client, user='dude', password='resu')
    assert b'Welcome to the house chores' in rv.data
    assert b'Wrong username / password combination' not in rv.data

def test_add_user_with_double_name(client):
    """Test adding a new user
    """
    login(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>dude</td><td>user</td>' not in rv.data.replace('\n','').replace('\t','')
    rv=client.post('/new_user', data=dict(name='dude', roles=2), follow_redirects=True)
    assert b'New user added' in rv.data
    assert b'<td>dude</td><td>user</td>' in rv.data.replace('\n','').replace('\t','')
    rv=client.post('/new_user', data=dict(name='dude', roles=2), follow_redirects=True)
    assert b'already exists' in rv.data
    assert b'New user added' not in rv.data

def test_add_user_non_admin(client):
    """Test adding a new user as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>dude</td><td>user</td>' not in rv.data.replace('\n','').replace('\t','')
    rv=client.post('/new_user', data=dict(name='dude', roles=2), follow_redirects=True)
    assert b'New user added' not in rv.data
    assert b'<td>dude</td><td>user</td>' not in rv.data.replace('\n','').replace('\t','')
    rv=client.get('/logout', follow_redirects=True)
    rv=login(client, user='dude', password='resu')
    assert b'Welcome to the house chores' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_remove_user(client):
    """Test removing a user
    """
    login(client)
    sample_db(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>random</td><td>user</td>' in rv.data.replace('\n','').replace('\t','')
    rv=client.get('/delete_user/4', follow_redirects=True)
    assert b'User removed' in rv.data
    assert b'<td>random</td><td>user</td>' not in rv.data.replace('\n','').replace('\t','')

def test_remove_user_non_admin(client):
    """Test removing a user as normal user
    """
    login(client)
    sample_db(client)
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    rv=client.get('/delete_user/4', follow_redirects=True)
    assert b'User removed' not in rv.data

def test_edit_user(client):
    """Test user chore
    """
    login(client)
    sample_db(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>newname</td>' not in rv.data
    assert b'<td>newname</td><td>admin</td>' not in rv.data.replace('\n','').replace('\t','')
    #edit user
    rv=client.post('/edit_user', data=dict(person='newname', role=1, id=3, passw=''), follow_redirects=True)
    assert b'User updated' in rv.data
    assert b'<td>newname</td><td>admin</td>' in rv.data.replace('\n','').replace('\t','')

def test_edit_user_to_existing_username(client):
    """Test user chore
    """
    login(client)
    sample_db(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>newname</td>' not in rv.data
    assert b'<td>newname</td><td>admin</td>' not in rv.data.replace('\n','').replace('\t','')
    #edit user
    rv=client.post('/edit_user', data=dict(person='admin', role=1, id=3, passw=''), follow_redirects=True)
    assert b'already exists' in rv.data
    assert b'User updated' not in rv.data

def test_edit_user_non_admin(client):
    """Test user chore as normal user
    """
    login(client)
    sample_db(client)
    rv=client.get('/user_admin', follow_redirects=True)
    assert b'<td>newname</td>' not in rv.data
    assert b'<td>newname</td><td>admin</td>' not in rv.data.replace('\n','').replace('\t','')
    #change user
    client.get('logout', follow_redirects=True)
    login(client, user='random', password='asd')
    #edit user
    rv=client.post('/edit_user', data=dict(person='newname', role=1, id=3, passw=''), follow_redirects=True)
    assert b'User updated' not in rv.data

### statistics
def test_show_stats(client):
    """Test the statistics page
    """
    login(client)
    sample_db(client)
    rv=client.get('/stats', follow_redirects=True)
    assert b'Statistics' in rv.data
    assert b'Top chores' in rv.data
    assert b'Who does what' in rv.data
    assert b'dishes' in rv.data #dishes should be done in sample db

### download database
def test_download_database(client):
    """Test the xml download from the database
    """
    login(client)
    sample_db(client)
    rv=client.get('/export_xml', follow_redirects=True)
    assert b'You can download the xml' in rv.data
    rv=client.get('download_xml')
    assert b'<actions>' in rv.data
    assert b'<roles>' in rv.data
    assert b'<chores>' in rv.data
    assert b'<persons>' in rv.data
    assert b'dishes' in rv.data
    assert b'random' in rv.data
    assert b'admin' in rv.data
    assert b'2015-08-01' in rv.data

### version numbers
def test_version_numbers(client):
    login(client)
    rv=client.get('/')
    assert b'Current version of application' in rv.data
    assert b'Current version of database' in rv.data

### paging
def test_paging_overview(client):
    """Test: After loading the sample data, the overview page
    should show some paging
    """
    login(client)
    sample_db(client)
    rv=client.get('/overview')
    assert b'<td>dishes</td>' in rv.data
    assert b'Current page' not in rv.data
    with housechores.app.app_context():
        db=housechores.get_db()
        db.execute("update meta set message='3' where key='actions_per_page'")
        db.commit()
    rv=client.get('/overview')
    assert b'<td>dishes</td>' in rv.data
    assert b'Current page' in rv.data
    rv=client.get('/overview/2', follow_redirects=True)
    assert b'Current page' in rv.data

if __name__=='__main__':
    pytest.main(['-vv'])
