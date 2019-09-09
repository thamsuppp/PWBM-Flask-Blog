#Video 5: Only purpose of this file is to run the application. (This was original flaskblog but most stuff taken out)

#Will import from __init__.py when importing from package
from flaskblog import create_app

#Create app, using Config class as default
app = create_app()

#If module imported somewhere else, then __name__ is the other module. So this will only be run if the flaskblog.py script  is run itself
if __name__ == '__main__':
    app.run(debug=True)