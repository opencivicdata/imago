import pymongo
from django.conf import settings

# http://docs.mongodb.org/manual/reference/connection-string/
mongo_uri = getattr(settings, 'IMAGO_MONGO_URI', 'localhost')
mongo_db = getattr(settings, 'IMAGO_MONGO_DATABASE', 'opencivicdata')

db = pymongo.Connection(mongo_uri)[mongo_db]
