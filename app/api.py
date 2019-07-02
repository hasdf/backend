import re

from functools import wraps
from flask import Blueprint, request, jsonify, abort, redirect, url_for,\
                  make_response, Response, current_app, render_template
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from geojson import Feature, FeatureCollection
from datetime import datetime
from app.models import db, Map, Feature as MapFeature
from app.grid import Grid


api = Blueprint('API', __name__)
CORS(api)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'X-Map' not in request.headers or 'X-Token' not in request.headers:
            abort(401)

        map_id = request.headers.get('X-Map')
        token = request.headers.get('X-Token')

        if not map_id or not token:
            abort(400)

        obj = Map.get(map_id)
        if not obj or not obj.check_token(token):
            abort(401)

        return f(*args, **kwargs)

    return decorated_function


@api.route('/api/maps/<string:map_id>/auth')
def auth(map_id):
    secret = request.headers.get('X-Secret', '')
    obj = Map.get(map_id)

    if not obj or not secret:
        abort(400)  # bad request - invalid input

    if not safe_str_cmp(secret, obj.secret):
        abort(401)  # forbidden - secrets do not match

    return jsonify(token=obj.gen_token())


@api.route('/api/maps/')
@api.route('/api/maps')
def maps():
    return jsonify([m.to_dict() for m in Map.all()])


def _parse_datetime(_datetime):
    if not _datetime:
        _datetime = datetime.now()
    if 'date' in request.json:
        _date = datetime.strptime(request.json['date'], '%Y-%m-%d')
        _datetime.replace(year=_date.year, month=_date.month, day=_date.day)
    if 'time' in request.json:
        _time = datetime.strptime(request.json['time'], '%H:%M')
        _datetime.replace(hour=_time.hour, minute=_time.minute)
    if 'datetime' in request.json:
        _datetime = datetime.strptime(request.json['datetime'], '%Y-%m-%d %H:%M')

    return _datetime

@api.route('/api/maps/', methods=['POST'])
@api.route('/api/maps', methods=['POST'])
def maps_new():
    if ('name' not in request.json):
        abort(400)

    json = request.json
    name = json['name']

    if (Map.get(json['name'])):
        return make_response(jsonify(name='Map already exists. Use another name!'), 400)

    m = Map(name)
    for key in ['name', 'bbox', 'description', 'place', 'attributes']:
        if key in json and json[key]:
            setattr(m, key, json[key])

    if 'datetime' in json:
        m.datetime = _parse_datetime()

    db.session.add(m)
    db.session.commit()

    return make_response(jsonify(m.to_dict(secret_included=True)), 201)


@api.route('/api/maps/<string:map_id>/')
@api.route('/api/maps/<string:map_id>')
def map_get(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)
    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['PATCH'])
@api.route('/api/maps/<string:map_id>', methods=['PATCH'])
@login_required
def map_edit(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    json = request.json
    if 'name' in json:
        m_for_name = Map.get(json['name'])
        if (m_for_name and m.id != m_for_name.id):
            error = 'Map already exists. Use another name!'
            return make_response(jsonify(name=error), 400)


    for key in ['name', 'bbox', 'description', 'place', 'attributes', 'lifespan', 'published']:
        if key in json and json[key]:
                setattr(m, key, json[key])

    if 'datetime' in json:
        m.datetime = _parse_datetime(m.datetime)

    db.session.add(m)
    db.session.commit()

    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['DELETE'])
@api.route('/api/maps/<string:map_id>', methods=['DELETE'])
@login_required
def map_delete(map_id):
    Map.delete(map_id)
    return ('', 204)


@api.route('/api/maps/<string:map_id>/features')
def map_features(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features))


@api.route('/api/maps/<string:map_id>/features', methods=['POST'])
@login_required
def map_features_new(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)

    if not request.json or not Feature(request.json).is_valid:
        abort(400)

    # TODO: strip input data
    feature = MapFeature(request.json)
    m.features.append(feature)
    db.session.add(m)
    db.session.commit()

    return make_response(jsonify(feature.to_dict()), 201)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['DELETE'])
@login_required
def map_feature_delete(map_id, feature_id):
    f = MapFeature.get(feature_id)
    if not f:
        abort(404)

    db.session.delete(f)
    db.session.commit()

    return ('', 200)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['PUT', 'PATCH'])
@login_required
def map_feature_edit(map_id, feature_id):
    f = MapFeature.get(feature_id)
    if not f:
        abort(404)

    if not request.json or not Feature(request.json).is_valid:
        abort(400)

    if 'properties' in request.json:
        props = request.json['properties']
        if 'iconColor' in props:
            # ensure that we deal with hex values (not rgb(r,g,b))
            if props['iconColor'].startswith('rgb'):
                rgb = re.findall(r'\d+', props['iconColor'])
                iconColor = ''.join([('%02x' % int(x)) for x in rgb])
                props['iconColor'] = '#' + iconColor
        f.style = props

    if 'geometry' in request.json:
        f.geo = request.json['geometry']

    db.session.add(f)
    db.session.commit()

    return jsonify(f.to_dict())


@api.route('/api/grid/<string:bbox>')
def grid_get(bbox):
    return jsonify(Grid(*map(float, bbox.split(','))).generate())


@api.route('/api/maps/<string:map_id>/grid')
def map_get_grid(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)
    return jsonify(m.grid)


@api.route('/api/maps/<string:map_id>/geojson')
def map_export_geojson(map_id):
    m = Map.get(map_id)
    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features, properties=m.to_dict(False)))
