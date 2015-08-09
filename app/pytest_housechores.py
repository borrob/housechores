"""
Unit tests for housechores
Based on pytest

Run via::
>>>> py.test pytest_housechores.py
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
    assert b'dishes' in rv.data
