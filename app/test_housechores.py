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
    assert b'Hello there!' in rv.data

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

def test_add_chore(client):
    """Test adding a chore
    """
    login(client)
    rv=client.post('/new_chore', data=dict(chore='thisisanewchore'),follow_redirects=True)
    assert b'New chore added' in rv.data #test the flash message
    assert b'<td>thisisanewchore</td>' in rv.data #test the actual insert

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

### login
def test_login_required(client):
    """not login in should get you nowhere
    """
    rv=client.get('/', follow_redirects=True)
    assert b'Login first!' in rv.data
    assert b'Hello there' not in rv.data
    login(client)
    rv=client.get('/', follow_redirects=True)
    assert b'Login first!' not in rv.data
    assert b'Hello there' in rv.data

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
    assert b'Hello there' in rv.data
    assert b'Wrong username / password combination' not in rv.data

def test_login2(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, user='wronguser')
    assert b'Hello there' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_login3(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, password='wrongpassword')
    assert b'Hello there' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_login4(client):
    """Test correct and wrong username and passwords
    """
    rv=login(client, user='wronguser', password='wrongpassword')
    assert b'Hello there' not in rv.data
    assert b'Wrong username / password combination' in rv.data

def test_logout(client):
    """After logout no page should be available anymore
    """
    rv=login(client)
    assert b'Hello there' in rv.data
    rv=client.get('/logout', follow_redirects=True)
    assert b'You were logged out' in rv.data
    rv=client.get('/', follow_redirects=True)
    assert b'Hello there' not in rv.data
    assert b'Login first' in rv.data

if __name__=='__main__':
    pytest.main(['-vv'])
