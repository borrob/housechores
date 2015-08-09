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

def sample_db(client):
    """Fill the database with sample data
    """
    client.get('/filldbsampledata',follow_redirects=True)

def test_Root(client):
    """Test if the application is running
    """
    rv=client.get('/')
    assert b'Hello there!' in rv.data

def test_empty_overviewpage(client):
    """Test: with an empty database, the overview page is blank
    The page should return 'No chores yet'
    """
    rv=client.get('/overview')
    assert b'No chores yet' in rv.data

def test_sample_data_loaded(client):
    """Test: After loading the sample data, the overview page
    should return something about 'dishes'
    """
    sample_db(client)
    rv=client.get('/overview')
    assert b'<td>dishes</td>' in rv.data

def test_remove_action(client):
    """Test deleting an action
    """
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

if __name__=='__main__':
    pytest.main()
