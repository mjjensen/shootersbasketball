from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from app import db, app
"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""


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

#     competition = relationship(
#         'Competitions', backref=backref('competition_teams', lazy=True),
#         foreign_keys=[Teams.competition_id]  # @UndefinedVariable
#     )
#     team_manager = relationship(
#         'People', backref=backref('team_manager_teams', lazy=True),
#         foreign_keys=[Teams.team_manager_id]  # @UndefinedVariable
#     )
#     coach = relationship(
#         'People', backref=backref('coach_teams', lazy=True),
#         foreign_keys=[Teams.coach_id]  # @UndefinedVariable
#     )
#     asst_coach = relationship(
#         'People', backref=backref('asst_coach_teams', lazy=True),
#         foreign_keys=[Teams.asst_coach_id]  # @UndefinedVariable
#     )
#     session = relationship(
#         'Sessions', backref=backref('session_teams', lazy=True),
#         foreign_keys=[Teams.session_id]  # @UndefinedVariable
#     )
#     old_session = relationship(
#         'Sessions', backref=backref('old_session_teams', lazy=True),
#         foreign_keys=[Teams.old_session_id]  # @UndefinedVariable
#     )


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

#     venue = relationship(
#         'Venues', backref=backref('venue_sessions', lazy=True),
#         foreign_keys=[Sessions.venue_id]  # @UndefinedVariable
#     )