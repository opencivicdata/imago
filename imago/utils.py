import pymongo
from .core import db, elasticsearch
from .exceptions import APIError

def dict_to_mongo_query(params, allowed_fields):
    query = {}

    for key, value in params.iteritems():
        if '__' in key:
            key, operator = key.split('__', 1)
        else:
            operator = None

        if key in allowed_fields:
            param_func = allowed_fields[key]
            if param_func:
                value = param_func(value)
        elif operator != 'id':
            continue

        if not operator:
            query[key] = value
        elif operator in ('gt', 'gte', 'lt', 'lte', 'ne'):
            query[key] = {'$'+operator: value}
        elif operator in ('all', 'in', 'nin'):
            query[key] = {'$'+operator: value.split(',')}
        elif operator == 'id':
            query['identifiers'] = {'$elemMatch': {'scheme': key,
                                                   'identifier': value}
                                   }
        else:
            raise APIError('invalid operator: ' + operator)

        return query


class BillSearchResults(object):
    def __init__(self, es_search, mongo_query, sort, fields):
        self.es_search = es_search
        self.mongo_query = mongo_query
        self.sort_field = sort
        self.fields = fields
        self._len = None
        if sort in ('first', 'last', 'signed', 'passed_lower', 'passed_upper'):
            self.sort_field = 'action_dates.' + sort
        elif sort in ('updated_at', 'created_at'):
            self.sort_field = sort
        else:
            self.sort_field = 'action_dates.last'

    def __len__(self):
        if not self._len:
            if self.es_search:
                # TODO: change this eventually
                resp = elasticsearch.count(self.es_search['query'],
                                           index='billy', doc_type='bills')
                if not resp['_shards']['successful']:
                    # if we get a parse exception, simplify to a simple text match
                    if 'ParseException' in resp['_shards']['failures'][0]['reason']:
                        fquery = self.es_search['query']['filtered']['query']
                        fquery['match'] = {'_all': fquery['query_string']['query']}
                        fquery.pop('query_string')
                        resp = elasticsearch.count(self.es_search['query'],
                                                   index='billy', doc_type='bills')
                    else:
                        raise Exception('ElasticSearch error: ' + resp['_shards']['failures'])
                self._len = resp['count']
            else:
                self._len = db.bills.find(self.mongo_query).count()
        return self._len

    def __getitem__(self, key):
        start = 0
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop or len(self)
            if key.step:
                raise KeyError('step is not permitted')
        elif isinstance(key, int):
            start = key
            stop = key + 1

        if self.es_search:
            search = dict(self.es_search)
            # TODO: change bill_id to name?
            search['sort'] = [{self.sort_field: 'desc'}, 'bill_id']
            search['from'] = start
            search['size'] = stop-start
            es_result = elasticsearch.search(search, index='billy', doc_type='bills')
            _mongo_query = {'identifiers.identifier': {'$in': [r['_id'] for r in es_result['hits']['hits']]}}
            return db.bills.find(_mongo_query, fields=self.fields).sort(
                [(self.sort_field, pymongo.DESCENDING), ('name', pymongo.ASCENDING)]
            )
        else:
            return db.bills.find(self.mongo_query, fields=self.fields).sort(
                [(self.sort, pymongo.DESCENDING)]
            ).skip(start).limit(stop-start)


def bill_search(query, allowed_fields, bill_fields, sort):
    use_elasticsearch = False
    mongo_filter = {}
    es_terms = []

    if 'q' in query:
        q = query['q']
        use_elasticsearch = True    # allow this to be turned off

        # hack to stop spammers
        if '<a href' in q:
            raise PermissionDenied('html detected')

        # pull out the fields
        for key, value in query.iteritems():
            if '__' in key:
                key, operator = key.split('__', 1)
            else:
                operator = None

            if key in allowed_fields:
                param_func = allowed_fields[key]
                if param_func:
                    value = param_func(value)
            elif operator != 'id':
                continue

            if not operator:
                es_terms.append({'term': {key: value}})
            elif operator in ('gt', 'gte', 'lt', 'lte'):
                es_terms.append({'range': {key: {operator: value}}})
            elif operator == 'all':
                for val in value.split(','):
                    es_terms.append({key: val})
            elif operator == 'in':
                query[key] = {'$'+operator: value.split(',')}
            elif operator in ('id', 'ne', 'nin'):
                raise APIError('cannot combine full text search and __%s operator' % operator)
            else:
                raise APIError('invalid operator: ' + operator)

        search = {'query': {'query_string': {'fields': ['text', 'title'],
                                             'default_operator': 'AND',
                                             'query': q}}}
        if es_terms:
            search['filter'] = {'and': es_terms}
            search = {'query': {'filtered': search}}
        search['fields'] = []
        return BillSearchResults(search, None, sort, bill_fields)

    else:
        mongo_filter = dict_to_mongo_query(query, allowed_fields)
        return BillSearchResults(None, mongo_filter, sort, bill_fields)
