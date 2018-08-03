from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import BaseView, ModelView, expose, has_access
from flask_appbuilder.forms import DynamicForm
from wtforms.fields.core import StringField
from wtforms.validators import DataRequired
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.views import SimpleFormView
from flask.helpers import flash
from app import appbuilder, db
from app.models import Competitions, People, Venues, Teams, Sessions

"""
    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(MyModelView, "My View", icon="fa-folder-open-o",
        category="My Category", category_icon='fa-envelope')
"""


class MyView(BaseView):

    default_view = 'method1'

    @expose('/method1/')
    @has_access
    def method1(self):
        # do something with param1
        # and return to previous page or index
        return 'Hello'

    @expose('/method2/<string:param1>')
    @has_access
    def method2(self, param1):
        # do something with param1
        # and render template with param
        param1 = 'Goodbye %s' % (param1)
        return param1

    @expose('/method3/<string:param1>')
    @has_access
    def method3(self, param1):
        # do something with param1
        # and render template with param
        param1 = 'Goodbye %s' % (param1)
        self.update_redirect()
        return self.render_template('method3.html', param1=param1)


class MyForm(DynamicForm):
    field1 = StringField(('Field1'),
                         description=('Your field number one!'),
                         validators=[DataRequired()],
                         widget=BS3TextFieldWidget())
    field2 = StringField(('Field2'),
                         description=('Your field number two!'),
                         widget=BS3TextFieldWidget())


class MyFormView(SimpleFormView):
    form = MyForm
    form_title = 'This is my first form view'
    message = 'My form submitted, form=%s'

    def form_get(self, form):
        form.field1.data = 'This was prefilled'

    def form_post(self, form):
        # post process form
        flash(self.message % (form), 'info')


class CompetitionsModelView(ModelView):
    datamodel = SQLAInterface(Competitions)


class PeopleModelView(ModelView):
    datamodel = SQLAInterface(People)

    list_columns = ['name', 'email', 'mobile', 'wwc_number', 'wwc_expiry',
                    'postal_address', 'photo', 'dob', 'bv_mpd_expiry']

    show_fieldsets = [
                        (
                            'Summary',
                            {'fields': ['name', 'email', 'mobile']}
                        ),
                        (
                            'Personal Info',
                            {'fields': ['wwc_number', 'wwc_expiry',
                                        'postal_address', 'dob',
                                        'bv_mpd_expiry'],
                             'expanded': False}
                        ),
                     ]


class TeamManagerModelView(PeopleModelView):
    pass


class CoachModelView(PeopleModelView):
    pass


class AsstCoachModelView(PeopleModelView):
    pass


class SessionsModelView(ModelView):
    datamodel = SQLAInterface(Sessions)


class CurTSessionModelView(SessionsModelView):
    pass


class OldTSessionModelView(SessionsModelView):
    pass


class VenuesModelView(Venues):
    pass


class TeamsModelView(ModelView):
    datamodel = SQLAInterface(Teams)
    related_views = [CompetitionsModelView, TeamManagerModelView,
                     CoachModelView, AsstCoachModelView,
                     CurTSessionModelView, OldTSessionModelView]


appbuilder.add_view(MyView, 'Method1', category='My View')
appbuilder.add_link('Method2', href='/myview/method2/john', category='My View')
appbuilder.add_link('Method3', href='/myview/method3/john', category='My View')
appbuilder.add_view(MyFormView, "My form View", icon="fa-group",
                    label=_('My form View'), category="My Forms",
                    category_icon="fa-cogs")

appbuilder.add_view(TeamsModelView, "List Teams",
                    icon="fa-folder-open-o", category="Teams",
                    category_icon="fa-envelope")

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(_e):
    return render_template('404.html', base_template=appbuilder.base_template,
                           appbuilder=appbuilder), 404


db.create_all()
