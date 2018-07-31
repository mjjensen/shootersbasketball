# coding: utf-8
from flask_appbuilder.models.mixins import AuditMixin
from app import db

"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""


class Competition(AuditMixin, db.Model):
    __tablename__ = 'competitions'
    __table_args__ = (
        db.CheckConstraint(u'age_group in (9,10,12,14,16,18,20,21)'),
        db.CheckConstraint(u"gender in ('F','M')"),
        db.CheckConstraint(u'section >= 1 and section <= 15')
    )

    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String, nullable=False)
    age_group = db.Column(db.Integer, nullable=False)
    section = db.Column(db.Integer, nullable=False)


class Person(AuditMixin, db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text)
    mobile = db.Column(db.Text)
    wwc_number = db.Column(db.Text)
    wwc_expiry = db.Column(db.DateTime)
    postal_address = db.Column(db.Text)
    photo = db.Column(db.LargeBinary)
    dob = db.Column(db.DateTime)
    bv_mpd_expiry = db.Column(db.DateTime)


class TSession(AuditMixin, db.Model):
    __tablename__ = 'sessions'
    __table_args__ = (
        db.CheckConstraint(u"active in ('false', 'true')"),
        db.CheckConstraint(u"day in ('None','Monday','Tuesday','Wednesday','Thursday','Friday','Sunday')"),
        db.CheckConstraint(u'duration in (0,45,60)'),
        db.CheckConstraint(u"time in ('None','3.30pm','3.45pm','4.00pm','4.15pm','4.30pm','4.45pm','5.00pm','5.15pm','5.30pm','5.45pm','6.00pm','6.15pm','6.30pm','6.45pm','7.00pm','7.15pm','7.30pm','7.45pm','8.00pm','8.15pm','8.30pm','9.00pm','9.15pm')")
    )

    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    venue = db.relationship('Venue', backref=db.backref('venue_sessions', lazy=True), foreign_keys=[venue_id])
    day = db.Column(db.Text, nullable=False)
    time = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Text, nullable=False, server_default=db.FetchedValue())


class Team(AuditMixin, db.Model):
    __tablename__ = 'teams'
    __table_args__ = (
        db.CheckConstraint(u"active in ('false','true')"),
        db.CheckConstraint(u"fspstate in ('','C','T','CT','N','CN','TN','CTN')")
    )

    team_name = db.Column(db.Text, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    competition = db.relationship('Competition', backref=db.backref('competition_teams', lazy=True), foreign_keys=[competition_id])
    team_manager_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    team_manager = db.relationship('Person', backref=db.backref('team_manager_teams', lazy=True), foreign_keys=[team_manager_id])
    coach_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    coach = db.relationship('Person', backref=db.backref('coach_teams', lazy=True), foreign_keys=[coach_id])
    asst_coach_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    asst_coach = db.relationship('Person', backref=db.backref('asst_coach_teams', lazy=True), foreign_keys=[asst_coach_id])
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    session = db.relationship('TSession', backref=db.backref('session_teams', lazy=True), foreign_keys=[session_id])
    old_session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), server_default=db.FetchedValue())
    old_session = db.relationship('TSession', backref=db.backref('old_session_teams', lazy=True), foreign_keys=[old_session_id])
    last_season_info = db.Column(db.Text)
    active = db.Column(db.Text, nullable=False, server_default=db.FetchedValue())
    fspstate = db.Column(db.String, server_default=db.FetchedValue())
    fspcode = db.Column(db.Text)
    fsppass = db.Column(db.Text)


class Venue(AuditMixin, db.Model):
    __tablename__ = 'venues'
    __table_args__ = (
        db.CheckConstraint(u'max_teams in (0,1,2)'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    max_teams = db.Column(db.Integer, nullable=False)
    abbrev = db.Column(db.Text, nullable=False)
