import pymongo
import pyelasticsearch
from django.conf import settings

# need to come up with a single config for this stuff?

# http://docs.mongodb.org/manual/reference/connection-string/
mongo_uri = getattr(settings, 'IMAGO_MONGO_URI', 'localhost')
mongo_db = getattr(settings, 'IMAGO_MONGO_DATABASE', 'opencivicdata')

db = pymongo.Connection(mongo_uri)[mongo_db]

if getattr(settings, 'ENABLE_ELASTICSEARCH', True):
    host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost')
    timeout = getattr(settings, 'ELASTICSEARCH_TIMEOUT', 60)
    elasticsearch = pyelasticsearch.ElasticSearch(host, timeout=timeout, revival_delay=0)
