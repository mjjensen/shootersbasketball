# coding: utf-8
"""
    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(MyModelView, "My View", icon="fa-folder-open-o",
    category="My Category", category_icon='fa-envelope')
"""
from flask import flash
from flask import render_template
from flask_appbuilder import BaseView, SimpleFormView, expose, has_access
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.forms import DynamicForm
from flask_babel import lazy_gettext as _
from wtforms import StringField
from wtforms.validators import DataRequired

from app import appbuilder, db


@appbuilder.app.errorhandler(404)
def page_not_found(_e):
    """
        Application wide 404 error handler
    """
    return render_template('404.html', base_template=appbuilder.base_template,
                           appbuilder=appbuilder), 404


db.create_all()


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


appbuilder.add_view(MyView, 'Method1', category='My View')
appbuilder.add_link('Method2', href='/myview/method2/john', category='My View')
appbuilder.add_link('Method3', href='/myview/method3/john', category='My View')
appbuilder.add_view(MyFormView, "My form View", icon="fa-group",
                    label=_('My form View'), category="My Forms",
                    category_icon="fa-cogs")
