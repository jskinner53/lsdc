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
    name = StringField(required=True, unique=True)
    description = StringField(required=True)
    bson_type = StringField()
    default_value = DynamicField()
    validation_routine_name = StringField()


class Types(DynamicDocument):
    parent_type = StringField(required=True)
    name = StringField(required=True, unique_with=parent_type)  # unique_with='owner'?  or base_type?
    description = StringField(required=True)
    field_list = ListField(ReferenceField(Field, dbref=True, reverse_delete_rule=mongoengine.DENY))
    version = StringField()


class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True, **args_dict)
    container_type = ReferenceField(Types, dbref=True, required=True,
                                    reverse_delete_rule=mongoengine.DENY)
    containerName = StringField(unique=True)

class Request(DynamicDocument):
    request_id = SequenceField(required=True, unique=True, **args_dict)
    timestamp = ComplexDateTimeField(required=True, default=datetime.datetime.now())
    request_type = ReferenceField(Types, dbref=True, required=True,
                                  reverse_delete_rule=mongoengine.DENY)

class Result(DynamicDocument):
    result_id = SequenceField(required=True, unique=True, **args_dict)
#    request_id = ReferenceField(Request, dbref=True, required=True,
#                                reverse_delete_rule=mongoengine.NULLIFY)
    request_id = ReferenceField(Request, dbref=True,
                                reverse_delete_rule=mongoengine.DENY)
    timestamp = ComplexDateTimeField(required=True, default=datetime.datetime.now())
    result_type = ReferenceField(Types, dbref=True, required=True,
                                 reverse_delete_rule=mongoengine.DENY)

class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True, **args_dict)

    # these are not required and not necessarily recommended!
    # they're mostly leftovers
    requestList = ListField(ReferenceField(Request, dbref=True,
                                           reverse_delete_rule=mongoengine.DENY))
    resultList = ListField(ReferenceField(Result, dbref=True,
                                          reverse_delete_rule=mongoengine.DENY))

    #owner = StringField(required=True)
    #sampleName = StringField(required=True, unique_with='owner')
    sampleName = StringField(required=True, unique=True)
    sample_type = ReferenceField(Types, dbref=True, required=True,
                                 reverse_delete_rule=mongoengine.DENY)


class BeamlineInfo(DynamicDocument):
    """generic store for arbitrary beamline info/settings
    """
    beamline_id = StringField(required=True)
    info_name = StringField(required=True, unique_with='beamline_id')
    info = DictField(required=True)

class UserSettings(DynamicDocument):
    """generic store for arbitrary user info/preferences
    """
    user_id = StringField(required=True)
    settings_name = StringField(required=True, unique_with='user_id')
    settings = DictField(required=True)


class GenericFile(DynamicDocument):
    """ not for data!  just thumbnails, xtal pics, and stuff
    """
    data = BinaryField(required=True)


collections = [Field, Types, Container, Request, Result, Sample, BeamlineInfo, UserSettings, GenericFile]
