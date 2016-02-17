#WTForms / Flask-WTForms
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, validators

class QueryForm(Form):
    query = StringField('Team', [validators.DataRequired()])
    submit = SubmitField("Submit")
    '''
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
          return False
    '''
