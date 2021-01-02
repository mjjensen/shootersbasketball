'''
Created on 7 Jul. 2018

@author: jen117
'''

from __future__ import print_function

import os
from sqlalchemy import event
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import Session

from sbcilib.config import TEAMSDB_FILE
from sbcilib.utils import SbciEnum


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    # Will force sqlite constraint foreign keys

    # print('_set_sqlite_pragma: enabling foreign keys, conn={}, rec={}'
    #       .format(dbapi_connection, connection_record), file=sys.stderr)
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


def _classname_for_table(_base, tablename, _table):
    # print('classname_for_table: base={}, tablename={}, table={}'
    #       .format(base.__name__, tablename, table), file=sys.stderr)
    return str(tablename)


def _name_for_scalar_relationship(_base, _local_cls, referred_cls, constraint):
    # print('name_for_scalar_relationship: '
    #       'base={}, local_cls={}, referred_cls={}, constraint={}'
    #       .format(base.__name__, local_cls.__name__,
    #               referred_cls.__name__, constraint), file=sys.stderr)
    # print('constraint.column_keys={}'.format(constraint.column_keys),
    #       file=sys.stderr)
    # return referred_cls.__name__.lower()
    id_col = constraint.column_keys[0]
    if not id_col.endswith('_id'):
        return referred_cls.__name__.lower()
    return id_col[:-3]


def _name_for_collection_relationship(
        _base, _local_cls, referred_cls, constraint):
    # print('name_for_collection_relationship: '
    #       'base={}, local_cls={}, referred_cls={}, constraint={}'
    #       .format(base.__name__, local_cls.__name__,
    #               referred_cls.__name__, constraint), file=sys.stderr)
    # print('constraint.column_keys={}'.format(constraint.column_keys),
    #       file=sys.stderr)
    # return referred_cls.__name__.lower() + "_collection"
    id_col = constraint.column_keys[0]
    if not id_col.endswith('_id'):
        return referred_cls.__name__.lower() + '_collection'
    return id_col[:-3] + '_collection'


class TeamRole(SbciEnum):
    '''TODO'''
    COACH = 1, 'Coach'
    ASSISTANT_COACH = 2, 'Assistant Coach'
    TEAM_MANAGER = 3, 'Team Manager'


class SbciTeamsDB(object):
    '''TODO'''

    def __init__(self, verbose=0, *args, **kwds):
        super(SbciTeamsDB, self).__init__(*args, **kwds)

        if not os.access(TEAMSDB_FILE, os.R_OK | os.W_OK):
            raise RuntimeError('cannot access DB file ({}) for R/W!'
                               .format(TEAMSDB_FILE))

        self.Base = automap_base()

        self.engine = create_engine('sqlite:///' + TEAMSDB_FILE)

        self.Base.prepare(
            self.engine, reflect=True,
            classname_for_table=_classname_for_table,
            name_for_scalar_relationship=_name_for_scalar_relationship,
            name_for_collection_relationship=_name_for_collection_relationship
        )

        self.Venues = self.Base.classes.venues
        self.Roles = self.Base.classes.roles
        self.Sessions = self.Base.classes.sessions
        self.People = self.Base.classes.people
        self.Teams = self.Base.classes.teams

        if verbose > 1:
            for cls in (self.People, self.Venues, self.Teams, self.Sessions):
                print('{} = {}'.format(cls.__name__, dir(cls)))

        self.dbsession = Session(self.engine)

        self.venues_query = self.dbsession.query(self.Venues)
        self.roles_query = self.dbsession.query(self.Roles)
        self.sessions_query = self.dbsession.query(self.Sessions)
        self.people_query = self.dbsession.query(self.People)
        self.teams_query = self.dbsession.query(self.Teams)
