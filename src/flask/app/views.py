from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from app import appbuilder, db

from app.models import Competitions, People, Venues, Sessions, Teams

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


@appbuilder.app.errorhandler(404)
def page_not_found(_e):
    return render_template('404.html', base_template=appbuilder.base_template,
                           appbuilder=appbuilder), 404


class CompetitionsModelView(ModelView):
    datamodel = SQLAInterface(Competitions)


class PeopleModelView(ModelView):
    datamodel = SQLAInterface(People)

#     label_columns = {}

#     list_columns = ['name', 'email', 'mobile', 'wwc_number', 'wwc_expiry',
#                     'postal_address', 'photo', 'dob', 'bv_mpd_expiry']

#     show_fieldsets = [
#                         (
#                             'Summary',
#                             {'fields': ['name', 'email', 'mobile']}
#                         ),
#                         (
#                             'Personal Info',
#                             {'fields': ['wwc_number', 'wwc_expiry',
#                                         'postal_address', 'dob',
#                                         'bv_mpd_expiry'],
#                              'expanded': False}
#                         ),
#                      ]


class VenuesModelView(ModelView):
    datamodel = SQLAInterface(Venues)


class SessionsModelView(ModelView):
    datamodel = SQLAInterface(Sessions)
    related_views = [VenuesModelView]


class TeamsModelView(ModelView):
    datamodel = SQLAInterface(Teams)

#     related_views = [CompetitionsModelView, PeopleModelView, SessionsModelView]

    list_columns = ['team_name', 'competition', 'team_manager']


appbuilder.add_view(TeamsModelView, "List Teams",
                    icon="fa-folder-open-o", category="Teams",
                    category_icon="fa-envelope")
appbuilder.add_view(PeopleModelView, "List Coaches",
                    icon="fa-folder-open-o", category="People",
                    category_icon="fa-envelope")

# db.create_all()
