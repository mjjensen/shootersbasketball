from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app import db, app
"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""


# idea came from this: https://stackoverflow.com/a/36337815/2130789
db.reflect(app=app)


class Competitions(Model):
    __bind_key__ = 'teamsdb'
    __tablename__ = 'competitions'
    __table_args__ = (
        db.CheckConstraint(u'age_group in (9,10,12,14,16,18,20,21)'),
        db.CheckConstraint(u"gender in ('F','M')"),
        db.CheckConstraint(u'section >= 1 and section <= 15'),
        {'extend_existing': True}
    )


class People(Model):
    __bind_key__ = 'teamsdb'
    __tablename__ = 'people'
    __table_args__ = (
        {'extend_existing': True}
    )


class Venues(Model):
    __bind_key__ = 'teamsdb'
    __tablename__ = 'venues'
    __table_args__ = (
        db.CheckConstraint(u'max_teams in (0,1,2)'),
        {'extend_existing': True}
    )


class Teams(Model):
    __bind_key__ = 'teamsdb'
    __tablename__ = 'teams'
    __table_args__ = (
        db.CheckConstraint(u"active in ('false','true')"),
        db.CheckConstraint(u"fspstate in "
                           u"('','C','T','CT','N','CN','TN','CTN')"),
        {'extend_existing': True}
    )


class Sessions(Model):
    __bind_key__ = 'teamsdb'
    __tablename__ = 'sessions'
    __table_args__ = (
        db.CheckConstraint(u"active in ('false', 'true')"),
        db.CheckConstraint(u"day in ('None','Monday','Tuesday','Wednesday',"
                           u"'Thursday','Friday','Sunday')"),
        db.CheckConstraint(u'duration in (0,45,60)'),
        db.CheckConstraint(u"time in ('None','3.30pm','3.45pm','4.00pm',"
                           u"'4.15pm','4.30pm','4.45pm','5.00pm','5.15pm',"
                           u"'5.30pm','5.45pm','6.00pm','6.15pm','6.30pm',"
                           u"'6.45pm','7.00pm','7.15pm','7.30pm','7.45pm',"
                           u"'8.00pm','8.15pm','8.30pm','9.00pm','9.15pm')"),
        {'extend_existing': True}
    )
