DONE: 'Setup app server'
DONE: 'Create interface with Bootstrap'

TODO: 'csv to dataframe extraction'
TODO: 'pdf to dataframe extraction'
TODO: 'split order into aps and non aps parts'
TODO: 'make pdf from split order'
TODO: 'make test with systems from csv -optionally extract all posiblle systems from LOCKBASE'
TODO: 'make aps file from order'
TODO: 'unitest of aps files - comparision with orders'

"""    /yourapp  
        /run.py  
        /config.py  
        /app  
            /__init__.py
            /views.py  
            /models.py  
            /static/  
                /main.css
            /templates/  
                /base.html  
        /requirements.txt  
        /yourappenv

run.py - contains the actual python code that will import the app and start the development server.
config.py - stores configurations for your app.
__init__.py - initializes your application creating a Flask app instance.
views.py - this is where routes are defined.
models.py - this is where you define models for your application.
static - contains static files i.e. CSS, Javascript, images
templates - this is where you store your html templates i.e. index.html, layout.html
requirements.txt - this is where you store your package dependancies, you can use pip
yourappenv - your virtual environment for development
 """

"""
 /home/user/Projects/flask-tutorial
├── flaskr/
│   ├── __init__.py
│   ├── db.py
│   ├── schema.sql
│   ├── auth.py
│   ├── blog.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── blog/
│   │       ├── create.html
│   │       ├── index.html
│   │       └── update.html
│   └── static/
│       └── style.css
├── tests/
│   ├── conftest.py
│   ├── data.sql
│   ├── test_factory.py
│   ├── test_db.py
│   ├── test_auth.py
│   └── test_blog.py
├── venv/
├── setup.py
└── MANIFEST.in
 """