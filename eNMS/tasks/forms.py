from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextField
)


class SchedulingForm(FlaskForm):
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    waiting_time = IntegerField(default=0)
    frequency = TextField()
    run_immediately = BooleanField()
    do_not_run = BooleanField(default=True)
    service_type = SelectField()
    devices = SelectMultipleField()
    pools = SelectMultipleField()
    job = SelectField()


class CompareLogsForm(FlaskForm):
    first_version = SelectField()
    second_version = SelectField()
    first_device = SelectField()
    second_device = SelectField()
