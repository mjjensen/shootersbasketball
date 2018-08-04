import logging
import os
from flask import Flask
from flask_appbuilder import SQLA, AppBuilder
from sqlalchemy.ext.automap import automap_base

"""
 Logging configuration
"""

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object('config')
db = SQLA(app)
db.Model = automap_base(db.Model)
appbuilder = AppBuilder(app, db.session)


from sbcilib.teamsdb import SbciTeamsDB  # @IgnorePep8
teamsdb = SbciTeamsDB(config={
    'db_teams_file': app.config['TEAMS_FILE'],
    'db_teams_url':  'sqlite:///' + app.config['TEAMS_FILE'],
})

""""""
from sqlalchemy.engine import Engine  # @IgnorePep8
from sqlalchemy import event  # @IgnorePep8


# Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


""""""

from app import views  # @IgnorePep8
