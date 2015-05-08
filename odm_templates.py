from mongoengine import (DynamicDocument, DynamicEmbeddedDocument)
from mongoengine import (SequenceField, ListField, EmbeddedDocumentField) 


class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True)

class Request(DynamicEmbeddedDocument):
    request_id = SequenceField(required=True, unique=True)
    # unique doesn't seem to be enforced!?

class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True)
    requestList = ListField(EmbeddedDocumentField(Request))
#    sampleName = StringField(required=True, unique_with='owner')
    # unique on request_id doesn't seem to be enforced even trying this
    meta = {'indexes': [
                       {'fields': {'requestList.request_id': 1},
                        'sparse': True, 'unique': True}
            ]}

class Raster(DynamicDocument):
    raster_id = SequenceField(required=True, unique=True)
