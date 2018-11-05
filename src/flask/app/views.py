# from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, MultipleView
from app import appbuilder

from app.models import Competitions, Venues, Roles, Sessions, People, Teams

"""
    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(MyModelView, "My View", icon="fa-folder-open-o",
        category="My Category", category_icon='fa-envelope')
"""

"""
    Application wide 404 error handler
"""


# @appbuilder.app.errorhandler(404)
# def page_not_found(_e):
#     return render_template('404.html', base_template=appbuilder.base_template,
#                            appbuilder=appbuilder), 404


# it appears that the model view classes are initialised before reflection so
# none of the columns are present - need to manually list them all


class CompetitionsModelView(ModelView):
    datamodel = SQLAInterface(Competitions)

    list_columns = ['id', 'gender', 'age_group', 'section', 'day']


class VenuesModelView(ModelView):
    datamodel = SQLAInterface(Venues)

    list_columns = ['id', 'name', 'max_teams', 'abbrev']


class RolesModelView(ModelView):
    datamodel = SQLAInterface(Roles)

    list_columns = ['id', 'role']


class SessionsModelView(ModelView):
    datamodel = SQLAInterface(Sessions)

    related_views = [VenuesModelView]

    list_columns = ['id', 'venue', 'day', 'time', 'duration', 'active']


class PeopleModelView(ModelView):
    datamodel = SQLAInterface(People)

    related_views = [RolesModelView]

#     search_columns = ['name', 'postal_address', 'role']

    list_columns = ['id', 'name', 'email', 'mobile', 'wwc_number',
                    'wwc_expiry', 'postal_address', 'dob',
                    'bv_mpd_expiry', 'role']

#     show_fieldsets = [
#                         (
#                             'Summary',
#                             {'fields': ['name', 'email', 'mobile']}
#                         ),
#                         (
#                             'Personal Info',
#                             {'fields': ['wwc_number', 'wwc_expiry',
#                                         'postal_address', 'photo', 'dob',
#                                         'bv_mpd_expiry', 'role'],
#                              'expanded': False}
#                         ),
#                      ]


class TeamsModelView(ModelView):
    datamodel = SQLAInterface(Teams)

    related_views = [CompetitionsModelView, PeopleModelView, SessionsModelView]

#     search_columns = ['team_name', 'competition',
#                       'team_manager', 'coach', 'asst_coach',
#                       'session', 'old_session']

    list_columns = ['id', 'team_name', 'competition',
                    'team_manager', 'coach', 'asst_coach',
                    'session', 'old_session', 'active']


class MultipleViewsExp(MultipleView):
    views = [TeamsModelView, PeopleModelView, SessionsModelView,
             RolesModelView, VenuesModelView, CompetitionsModelView]


# db.create_all()
appbuilder.add_view(CompetitionsModelView, "List Competitions",
                    icon="fa-folder-open-o", category="Competitions",
                    category_icon="fa-envelope")
appbuilder.add_view(VenuesModelView, "List Venues",
                    icon="fa-folder-open-o", category="Venues",
                    category_icon="fa-envelope")
appbuilder.add_view(RolesModelView, "List Roles",
                    icon="fa-folder-open-o", category="Roles",
                    category_icon="fa-envelope")
appbuilder.add_view(SessionsModelView, "List Sessions",
                    icon="fa-folder-open-o", category="Sessions",
                    category_icon="fa-envelope")
appbuilder.add_view(PeopleModelView, "List People",
                    icon="fa-folder-open-o", category="People",
                    category_icon="fa-envelope")
appbuilder.add_view(TeamsModelView, "List Teams",
                    icon="fa-folder-open-o", category="Teams",
                    category_icon="fa-envelope")
appbuilder.add_view(MultipleViewsExp, "Multiple Views",
                    icon="fa-envelope", category="Contacts")
