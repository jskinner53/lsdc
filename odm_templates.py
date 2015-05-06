from mongoengine import DynamicDocument
from mongoengine import SequenceField


class Sample(DynamicDocument):
    sample_id = SequenceField(required=True, unique=True)
#    sampleName = StringField(required=True, unique_with='owner')

class Container(DynamicDocument):
    container_id = SequenceField(required=True, unique=True)

class Raster(DynamicDocument):
    raster_id = SequenceField(required=True, unique=True)
