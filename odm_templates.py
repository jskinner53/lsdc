from mongoengine import (DynamicDocument, DynamicEmbeddedDocument)
from mongoengine import (SequenceField, ListField, EmbeddedDocumentField) 
from mongoengine import (StringField, DictField)   # for bl info, user settings, and types
import mongoengine

from distutils.version import LooseVersion

args_dict = {}
if LooseVersion(mongoengine.__version__) >= LooseVersion('0.7.0'):
    args_dict['sequence_name'] = 'None'


class Container(DynamicDocument):
    container_id = SequenceField(#collection_name='mongoengine.counters',
                                 #sequence_name='container',
                                 required=True, unique=True, **args_dict)

class Request(DynamicEmbeddedDocument):
    request_id = SequenceField(#collection_name='mongoengine.counters',
                               #sequence_name='request',
                               required=True, unique=True, **args_dict)
    # unique doesn't seem to be enforced!?

class Sample(DynamicDocument):
    sample_id = SequenceField(#collection_name='mongoengine.counters',
                              #sequence_name='sample',
                              required=True, unique=True, **args_dict)
    requestList = ListField(EmbeddedDocumentField(Request))
#    sampleName = StringField(required=True, unique_with='owner')
    # unique on request_id doesn't seem to be enforced even trying this
    meta = {'indexes': [
                       {'fields': {'requestList.request_id': 1},
                        'sparse': True, 'unique': True}
            ]}

class Raster(DynamicDocument):
    raster_id = SequenceField(#collection_name='mongoengine.counters',
                              #sequence_name='raster',
                              required=True, unique=True, **args_dict)


class BeamlineInfo(DynamicDocument):
    beamline_id = StringField(required=True)
    info_name = StringField(required=True, unique_with='beamline_id')
    info = DictField(required=True)

class UserSettings(DynamicDocument):
    user_id = StringField(required=True)
    settings_name = StringField(required=True, unique_with='user_id')
    settings = DictField(required=True)
