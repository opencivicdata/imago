import pyelasticsearch
from django.conf import settings

if getattr(settings, 'ENABLE_ELASTICSEARCH', True):
    host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost')
    timeout = getattr(settings, 'ELASTICSEARCH_TIMEOUT', 60)
    elasticsearch = pyelasticsearch.ElasticSearch(host, timeout=timeout, revival_delay=0)
