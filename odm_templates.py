from mongoengine import DynamicDocument


class Sample(DynamicDocument):
    pass
#    sample_id = StringField(required=True, unique=True)
#    sampleName = StringField(required=True, unique_with='owner')

class Container(DynamicDocument):
    pass
#    container_id = StringField(required=True, unique=True)

class Raster(DynamicDocument):
    pass
#    raster_id = StringField(required=True, unique=True)
