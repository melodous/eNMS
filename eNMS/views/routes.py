from flask import current_app, jsonify, render_template, request
from os.path import join
from simplekml import Kml

from eNMS.admin.models import Parameters
from eNMS.base.helpers import fetch, get, post
from eNMS.base.properties import (
    device_public_properties,
    device_subtypes,
    link_public_properties,
    link_subtype_to_color,
    pretty_names
)
from eNMS.logs.models import Log
from eNMS.objects.forms import AddDevice, AddLink
from eNMS.objects.models import Pool, Device, Link
from eNMS.views import bp, styles
from eNMS.views.forms import GoogleEarthForm, ViewOptionsForm


@get(bp, '/<view_type>_view', 'Views Section')
def view(view_type):
    add_link_form = AddLink(request.form)
    all_devices = Device.choices()
    add_link_form.source.choices = all_devices
    add_link_form.destination.choices = all_devices
    labels = {'device': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        labels = {
            'device': request.form['device_label'],
            'link': request.form['link_label']
        }
    if len(Device.query.all()) < 50:
        view = 'glearth'
    elif len(Device.query.all()) < 2000:
        view = 'leaflet'
    else:
        view = 'markercluster'
    if 'view' in request.form:
        view = request.form['view']
    # name to id
    name_to_id = {
        device.name: id for id, device in enumerate(Device.query.all())
    }
    return render_template(
        f'{view_type}_view.html',
        pools=Pool.query.all(),
        parameters=Parameters.query.one().serialized,
        view=view,
        view_options_form=ViewOptionsForm(request.form),
        google_earth_form=GoogleEarthForm(request.form),
        add_device_form=AddDevice(request.form),
        add_link_form=add_link_form,
        device_fields=device_public_properties,
        link_fields=link_public_properties,
        labels=labels,
        names=pretty_names,
        device_subtypes=device_subtypes,
        link_colors=link_subtype_to_color,
        name_to_id=name_to_id,
        devices=Device.serialize(),
        links=Link.serialize()
    )


@get(bp, '/export_to_google_earth', 'Views Section')
def export_to_google_earth():
    kml_file = Kml()
    for device in Device.query.all():
        point = kml_file.newpoint(name=device.name)
        point.coords = [(device.longitude, device.latitude)]
        point.style = styles[device.subtype]
        point.style.labelstyle.scale = request.form['label_size']
    for link in Link.query.all():
        line = kml_file.newlinestring(name=link.name)
        line.coords = [
            (link.source.longitude, link.source.latitude),
            (link.destination.longitude, link.destination.latitude)
        ]
        line.style = styles[link.type]
        line.style.linestyle.width = request.form['line_width']
    filepath = join(
        current_app.path,
        'google_earth',
        f'{request.form["name"]}.kmz'
    )
    kml_file.save(filepath)
    return jsonify({'success': True})


@post(bp, '/get_logs/<device_id>', 'Logs Section')
def get_logs(device_id):
    device_logs = [
        log.content for log in Log.query.all()
        if log.source == fetch(Device, id=device_id).ip_address
    ]
    return jsonify('\n'.join(device_logs) or True)
