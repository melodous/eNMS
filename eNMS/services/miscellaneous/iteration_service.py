from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from typing import Optional, Set
from wtforms import BooleanField, HiddenField, SelectField, StringField
from yaql import factory

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, InstanceField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class IterationService(Service):

    __tablename__ = "IterationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    origin_of_targets = Column(String(SMALL_STRING_LENGTH), default="iteration")
    iterated_job_id = Column(Integer, ForeignKey("Job.id"))
    iterated_job = relationship(
        "Job", primaryjoin="Job.id == IterationService.iterated_job_id"
    )
    origin_of_values = Column(String(SMALL_STRING_LENGTH), default="iteration_values")
    yaql_query_values = Column(String(SMALL_STRING_LENGTH), default="")
    iteration_values = Column(MutableDict.as_mutable(PickleType), default={})
    per_device_values = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "IterationService"}

    def compute_devices(self, payload: dict) -> Set["Device"]:
        if self.origin_of_targets == "iteration":
            return super().compute_devices(payload)
        else:
            return self.iterated_job.compute_devices(payload)

    def job(self, payload: dict, device: Optional[Device] = None, parent: Optional[Job] = None) -> dict:
        if self.origin_of_values == "iteration_values":
            values = self.iteration_values
        else:
            engine = factory.YaqlFactory().create()
            values = engine(self.yaql_query_values).evaluate(data=payload)
        if self.per_device_values:
            values = values[device.name]
        else:
            values = values
        results = {}
        for value in values:
            payload["iteration_variable"] = value
            results[value] = self.iterated_job.job(payload, device)
        return {"success": True, "Iteration values": values, **results}


class IterationForm(ServiceForm):
    form_type = HiddenField(default="IterationService")
    iterated_job = InstanceField("Iterated Job", instance_type="Job")
    origin_of_targets = SelectField(
        choices=(
            ("iteration", "Use Targets from Iteration Service"),
            ("iterated", "Use Targets from Iterated Service"),
        )
    )
    origin_of_values = SelectField(
        choices=(
            ("iteration_values", "Iteration Values Dictionary below"),
            ("yaql", "YaQL Query on the Payload"),
        )
    )
    iteration_values = DictField()
    yaql_query_values = StringField()
    per_device_values = BooleanField()
