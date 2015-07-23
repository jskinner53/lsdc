from mongoengine import (DynamicDocument, DynamicEmbeddedDocument)
from mongoengine import (SequenceField, ListField, EmbeddedDocumentField) 
from mongoengine import (StringField, DictField)   # for bl info, user settings, and types
import mongoengine

from distutils.version import LooseVersion

args_dict = {}
if LooseVersion(mongoengine.__version__) >= LooseVersion('0.7.0'):
    args_dict['sequence_name'] = 'None'


class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True, **args_dict)


class Request(DynamicEmbeddedDocument):
    # doh!  mongo doesn't currently enforce uniqueness
    # of embedded doc fields in a list field :(
    request_id = SequenceField(required=True, unique=True, **args_dict)

class Result(DynamicEmbeddedDocument):
    # doh!  mongo doesn't currently enforce uniqueness
    # of embedded doc fields in a list field :(
    result_id = SequenceField(required=True, unique=True, **args_dict)

class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True, **args_dict)
    requestList = ListField(EmbeddedDocumentField(Request))
    resultList = ListField(EmbeddedDocumentField(Result))
    #owner = StringField(required=True, unique_with='owner')
    #owner = StringField()
    #sampleName = StringField(required=True, unique_with='owner')
    sampleName = StringField(required=True)


class Raster(DynamicDocument):
    raster_id = SequenceField(required=True, unique=True, **args_dict)


class BeamlineInfo(DynamicDocument):
    beamline_id = StringField(required=True)
    info_name = StringField(required=True, unique_with='beamline_id')
    info = DictField(required=True)

class UserSettings(DynamicDocument):
    user_id = StringField(required=True)
    settings_name = StringField(required=True, unique_with='user_id')
    settings = DictField(required=True)
