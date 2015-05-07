from mongoengine import (DynamicDocument, DynamicEmbeddedDocument)
from mongoengine import (SequenceField, ListField, EmbeddedDocumentField) 


class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True)

class Request(DynamicEmbeddedDocument):
    request_id = SequenceField(required=True, unique=True)

class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True)
    requestList = ListField(EmbeddedDocumentField(Request))
#    sampleName = StringField(required=True, unique_with='owner')

class Raster(DynamicDocument):
    raster_id = SequenceField(required=True, unique=True)
