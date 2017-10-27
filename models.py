import os
import geojson

from grid import Grid
from shapely.geometry import shape, mapping, box
from sqlalchemy.ext.hybrid import hybrid_property
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature,\
                         SignatureExpired
from app import db


def gen_token():
    return os.urandom(24)


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    secret = db.Column(db.Binary, default=gen_token)
    public = db.Column(db.Boolean, default=True)
    _bbox = db.Column(Geometry('POLYGON'))
    features = db.relationship('Feature', backref='map', lazy=True)

    def __init__(self, name, bbox):
        self.name = name
        self._bbox = from_shape(box(*bbox))
        self.serializer = TimedJSONWebSignatureSerializer(self.secret,
                                                          expires_in=600)

    @property
    def legend(self):
        return {
            'Twitter': '@foo',
            'EA': '030 69 55555',
            'Datum': '30.06.2018'
        }

    @property
    def grid(self):
        return Grid(*self.bbox).generate(cells=12)

    @hybrid_property
    def bbox(self):
        return to_shape(self._bbox).bounds

    @bbox.setter
    def bbox(self, value):
        self._bbox = from_shape(shape(value))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'public': self.public,
            'bbox': self.bbox
        }

    def gen_token(self):
        return self.serializer.dumps(self.id)

    def check_token(self, token):
        try:
            self.serializer.loads(token)
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token

        return True


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'), nullable=False)
    _geo = db.Column(Geometry())
    style = db.Column(db.JSON)

    def __init__(self, data):
        self.geo = data

    @hybrid_property
    def geo(self):
        data = mapping(to_shape(self._geo))
        return data

    @geo.setter
    def geo(self, value):
        if 'properties' in value:
            self.style = value['properties']
        self._geo = from_shape(shape(value))

    def to_dict(self):
        properties = self.style.copy() if self.style else {}
        properties['id'] = self.id
        return geojson.Feature(geometry=self.geo, properties=properties)


db.create_all()
