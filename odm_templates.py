import datetime

from mongoengine import (DynamicDocument, DynamicEmbeddedDocument)
from mongoengine import (SequenceField, ListField, EmbeddedDocumentField,
                         ComplexDateTimeField, ReferenceField, DynamicField) 
from mongoengine import (StringField, DictField, BinaryField)   # for bl info, user settings, and types
import mongoengine

from distutils.version import LooseVersion

args_dict = {}
if LooseVersion(mongoengine.__version__) >= LooseVersion('0.7.0'):
    args_dict['sequence_name'] = 'None'


class Field(DynamicDocument):
    field_name = StringField(required=True, unique=True)
    description = StringField(required=True)
    ctype = StringField()
    default_value = DynamicField()
    validation_routine_name = StringField()


class Types(DynamicDocument):
    name = StringField(required=True, unique=True)  # unique_with='owner'
    description = StringField(required=True)
    base_type = StringField(required=True)
    field_list = ListField(ReferenceField(Field, dbref=True))
    version = StringField()


class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True, **args_dict)

class Request(DynamicDocument):
    # doh!  mongo doesn't currently enforce uniqueness
    # of embedded doc fields in a list field :(
    
    request_id = SequenceField(required=True, unique=True, **args_dict)
    timestamp = ComplexDateTimeField(required=True, default=datetime.datetime.now())
    request_type = ReferenceField(Types, dbref=True, required=True)

class Result(DynamicDocument):
    # doh!  mongo doesn't currently enforce uniqueness
    # of embedded doc fields in a list field :(
    result_id = SequenceField(required=True, unique=True, **args_dict)
    request_id = ReferenceField(Request, dbref=True, required=True)
    timestamp = ComplexDateTimeField(required=True, default=datetime.datetime.now())
    result_type = ReferenceField(Types, dbref=True, required=True)

class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True, **args_dict)
    requestList = ListField(ReferenceField(Request, dbref=True))
    resultList = ListField(ReferenceField(Result, dbref=True))
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


class GenericFile(DynamicDocument):
#    file_id = SequenceField(required=True, unique=True, **args_dict)
    data = BinaryField(required=True)


#class ObjectType(DynamicDocument):
#    name = StringField(required=True, unique=True)
#    base_type = StringField(required=True)

collections = [Field, Types, Container, Request, Result, Sample, Raster, BeamlineInfo, UserSettings, GenericFile]
