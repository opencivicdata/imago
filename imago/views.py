import json
from django.http import HttpResponse
from django.views.generic.base import View
from django.core.serializers.json import DateTimeAwareJSONEncoder
from imago.core import db


def _clamp(val, _min, _max):
    return _min if val < _min else _max if val > _max else val


def mongo_bulk_get(collection, ids):
    results = collection.find({'_id': {'$in': ids}})
    return {r['_id']: r for r in results}


class JsonView(View):
    """ Base view for writing API views

    Properties to set:
        collection - collection to query
        find_one - use find_one instead of find in lookup
            (optional - default False)
        default_fields - mongodb fields parameter if not specified
            (optional - defaults to all)
        per_page
            (optional- defaults to 100)
        query_params
            (optional defaults to [])
    """

    find_one = False
    default_fields = None
    per_page = 100
    query_params = ()

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        data = self.get_data(get_params, *args, **kwargs)

        if self.find_one:
            pass
        else:
            total = data.count()

            try:
                per_page = _clamp(
                    int(get_params.get('per_page', self.per_page)),
                    1, self.per_page
                )
            except ValueError:
                per_page = self.per_page

            try:
                page = _clamp(int(get_params.get('page', 0)),
                              0, total/per_page)
            except ValueError:
                page = 0

            data = list(data.skip(page*per_page).limit(per_page))
            data = {'results': data, 'meta': {'page': page,
                                              'per_page': per_page,
                                              'count': len(data),
                                              'total_count': total,
                                              'max_page': total/per_page,
                                             }
                   }

        data = json.dumps(self._clean(data), cls=DateTimeAwareJSONEncoder,
                          ensure_ascii=False)

        # JSONP
        cb = get_params.get('callback', None)
        if cb:
            return '{0}({1})'.format(cb, data)

        return HttpResponse(data)

    def get_data(self, get_params, *args, **kwargs):
        # make copy of get_params and pop things off
        fields = self.fields_from_request(get_params)
        sort = self.sort_from_request(get_params)
        query = self.query_from_request(get_params, *args, **kwargs)
        if self.find_one:
            result = self.collection.find_one(query, fields=fields)
        else:
            result = self.collection.find(query, fields=fields)
            if sort:
                result = result.sort(sort)

        return result

    def fields_from_request(self, get_params):
        fields = get_params.get('fields', None)

        if not fields:
            return self.default_fields
        else:
            d = {field: 1 for field in fields.split(',')}
            d['_id'] = d.pop('id', 1)
            d['_type'] = 1
            return d

    def sort_from_request(self, get_params):
        sort = get_params.get('sort', None)
        return sort

    def query_from_request(self, get_params, *args):
        query = {}
        for key in get_params:
            if key in self.query_params or key.startswith('id:'):
                if key.endswith('__lt'):
                    query[key[:-4]] = {'$lt': get_params[key]}
                elif key.endswith('__gt'):
                    query[key[:-4]] = {'$gt': get_params[key]}
                elif key.startswith('id:'):
                    query['identifiers'] = {'scheme': key[3:],
                                            'identifier': get_params[key]}
                else:
                    query[key] = get_params[key]
        return query

    def _clean(self, obj):
        if isinstance(obj, dict):
            if '_id' in obj:
                obj['id'] = obj['_id']

            for key, value in obj.items():
                if key.startswith('_'):
                    del obj[key]
                else:
                    obj[key] = self._clean(value)
        elif isinstance(obj, list):
            obj = [self._clean(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            obj = self._clean(obj.__dict__)

        return obj


class DetailView(JsonView):
    find_one = True

    def query_from_request(self, get_params, id):
        return {'_id': id}


class MetadataDetail(DetailView):
    collection = db.metadata



class OrganizationDetail(DetailView):
    collection = db.organizations

    def get_data(self, *args, **kwargs):
        data = super(OrganizationDetail, self).get_data(*args, **kwargs)
        data['memberships'] = list(db.memberships.find(
            {'organization_id': data['_id']}))

        people = mongo_bulk_get(
            db.people,
            [m['person_id'] for m in data['memberships'] if m['person_id']]
        )
        for m in data['memberships']:
            person_id = m['person_id']
            m['person'] = people[person_id] if person_id else None

        return data


class PersonDetail(DetailView):
    collection = db.people

    def get_data(self, *args, **kwargs):
        data = super(PersonDetail, self).get_data(*args, **kwargs)
        data['memberships'] = list(db.memberships.find(
            {'person_id': data['_id']}))

        orgs = mongo_bulk_get(
            db.organizations,
            [m['organization_id'] for m in data['memberships']
             if m['organization_id']]
        )
        for m in data['memberships']:
            org_id = m['organization_id']
            m['organization'] = orgs[org_id] if org_id else None

        return data

class BillDetail(DetailView):
    collection = db.bills



class MetadataList(JsonView):
    collection = db.metadata
    default_fields = {'name': 1, 'feature_flags': 1, 'chambers': 1, '_id': 1}

    def sort_from_request(self, request):
        return 'name'


class OrganizationList(JsonView):
    collection = db.organizations
    default_fields = {'contact_details': 0, 'sources': 0, 'posts': 0}
    query_params = ('classification', 'name', 'identifiers',
                    'founding_date', 'founding_date__gt', 'founding_date__lt',
                    'dissolution_date', 'dissolution_date__gt',
                    'dissolution_date__lt')


class PeopleList(JsonView):
    collection = db.people
    default_fields = {'contact_details': 0, 'sources': 0, 'extras': 0,
                      'links': 0, 'other_names': 0}
    query_params = ('name','gender')


class BillList(JsonView):
    collection = db.bills
    default_fields = {'sponsors': 0, 'sources': 0, 'actions': 0,
                      'links': 0, 'versions': 0, 'related_bills': 0,
                      'summaries': 0, 'subject': 0, 'other_titles': 0,
                      'documents': 0, 'other_names': 0
                     }
    query_params = ('name', 'name__in', 'chamber', 'session')
