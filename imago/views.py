import re
import json
import copy
import datetime
from collections import defaultdict
import pymongo
from django.http import HttpResponse
from django.views.generic.base import View
from django.core.serializers.json import DateTimeAwareJSONEncoder
from imago.core import db


class APIError(Exception):

    def __init__(self, msg, status=400):
        self.msg = msg
        self.status = status

    def __str__(self):
        return str(self.msg)



def _clamp(val, _min, _max):
    return _min if val < _min else _max if val > _max else val


def mongo_bulk_get(collection, ids):
    results = collection.find({'_id': {'$in': ids}})
    return {r['_id']: r for r in results}


def time_param(param):
    formats = ('%Y-%m-%d', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S',
               '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m', '%Y')
    dt = None
    if param == 'now':
        dt = datetime.datetime.utcnow()
    else:
        for format in formats:
            try:
                dt = datetime.datetime.strptime(param, format)
                break
            except ValueError:
                continue
        else:
            raise APIError('unrecognized datetime format: ' + param)
    return dt


def boolean_param(param):
    return param.lower() == 'true'


def fuzzy_string_param(param):
    return re.compile(r'\b{0}\b'.format(param), re.IGNORECASE)


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
        default_sort
        default_subfields
    """

    find_one = False
    default_fields = None
    per_page = 100
    query_params = {}
    default_sort = [('created_at', pymongo.DESCENDING)]
    default_subfields = None

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        try:
            data = self.get_data(get_params, *args, **kwargs)
        except APIError as e:
            resp = {'error': str(e)}
            data = json.dumps(resp)
            return HttpResponse(data, status=e.status)

        if not self.find_one:
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
            data = '{0}({1})'.format(cb, data)

        return HttpResponse(data)

    def get_data(self, get_params, *args, **kwargs):
        fields = self.fields_from_request(get_params)
        sort = self.sort_from_request(get_params)
        query = self.query_from_request(get_params, *args, **kwargs)
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
        sort = get_params.get('sort', self.default_sort)
        return sort

    def query_from_request(self, get_params, *args):
        query = {}

        for key, value in get_params.iteritems():
            # if this is an operator query, get the key & operator
            if '__' in key:
                key, operator = key.split('__', 1)
            else:
                operator = None

            # skip keys that aren't in query_params or ending with __id
            if key in self.query_params:
                param_func = self.query_params[key]
                if param_func:
                    value = param_func(value)
            elif operator != 'id':
                continue

            if not operator:
                query[key] = value
            elif operator in ('gt', 'gte', 'lt', 'lte', 'ne'):
                query[key] = {'$'+operator: value}
            elif operator in ('all', 'in', 'nin'):
                query[key] = {'$'+operator: value.split('|')}
            elif operator == 'id':
                query['identifiers'] = {'scheme': key,
                                        'identifier': value}
            else:
                raise APIError('invalid operator: ' + operator)

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

    def get_data(self, get_params, *args, **kwargs):
        fields = self.fields_from_request(get_params)
        query = self.query_from_request(get_params, *args, **kwargs)
        result = self.collection.find_one(query, fields=fields)

        if not result:
            raise APIError('no such object: ' + query['_id'], 404)

        return result


class MetadataDetail(DetailView):
    collection = db.metadata


class OrganizationDetail(DetailView):
    collection = db.organizations

    def get_data(self, *args, **kwargs):
        data = super(OrganizationDetail, self).get_data(*args, **kwargs)
        mem_fields = {'_id': 0}
        data['memberships'] = list(db.memberships.find(
            {'organization_id': data['_id']}, fields=mem_fields))

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
        mem_fields = {'_id': 0}
        data['memberships'] = list(db.memberships.find(
            {'person_id': data['_id']}, fields=mem_fields))

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

    def get_data(self, *args, **kwargs):
        data = super(BillDetail, self).get_data(*args, **kwargs)
        data['votes'] = list(db.votes.find({'bill.id': data['_id']}))
        return data


class EventDetail(DetailView):
    collection = db.events


class VoteDetail(DetailView):
    collection = db.votes


class MetadataList(JsonView):
    collection = db.metadata
    default_fields = {'terms': 0, 'session_details': 0, 'chambers': 0}
    default_sort = 'name'


class OrganizationList(JsonView):
    collection = db.organizations
    default_fields = {'contact_details': 0, 'sources': 0, 'posts': 0,
                      'founding_date': 0, 'dissolution_date': 0}
    query_params = {'classification': None,
                    'founding_date': None,
                    'dissolution_date': None,
                    'jurisdiction_id': None,
                    'parent_id': None,
                    'geography_id': None,
                    'chamber': None,
                    'name': fuzzy_string_param,
                    'updated_at': time_param,
                    'created_at': time_param}

class PeopleList(JsonView):
    collection = db.people
    default_fields = {'contact_details': 0, 'sources': 0, 'extras': 0,
                      'links': 0, 'birth_date': 0, 'death_date': 0}
    query_params = {'name': fuzzy_string_param,
                    'gender': None,
                    'birth_date': None,
                    'death_date': None,
                    'created_at': time_param,
                    'updated_at': time_param
                    'district': None,
                    # member_of
                    # ever_member_of
                   }

    def query_from_request(self, get_params, *args):
        query = super(PeopleList, self).query_from_request(get_params, *args)
        member_of = get_params.pop('member_of', [None])[0]
        ever_member_of = get_params.pop('ever_member_of', [None])[0]
        mem_specs = []

        if member_of and ever_member_of:
            raise APIError('cannot pass member_of and ever_member_of')
        elif member_of:
            mem_specs = [{'organization_id': _id, 'end_date': None} for _id in
                         member_of.split(',')]
        elif ever_member_of:
            mem_specs = [{'organization_id': _id} for _id in
                         member_of.split(',')]

        # intersection of resulting ids from multiple subqueries
        if mem_specs:
            ids = set(db.memberships.find(mem_specs[0]).distinct('person_id'))
            for spec in mem_specs[1:]:
                ids &= set(db.memberships.find(spec).distinct('person_id'))
            query['_id'] = {'$in': list(ids)}

        return query


class BillList(JsonView):
    collection = db.bills
    default_fields = {'sponsors': 0, 'sources': 0, 'actions': 0,
                      'links': 0, 'versions': 0, 'related_bills': 0,
                      'summaries': 0, 'other_titles': 0, 'documents': 0 }
    query_params = {'name': None,
                    'chamber': None,
                    'session': None,
                    'jurisdiction_id': None,
                    'type': None,
                    'subject': None,
                    'sponsors.id': None,
                    'created_at': time_param,
                    'updated_at': time_param}
    # TODO: other_names (everywhere)
    # TODO: title search?, text search, search_window, sponsorship, subject


class EventList(JsonView):
    collection = db.events
    default_fields = {'sources': 0}
    query_params = {'jurisdiction_id': None,
                    'when': time_param,
                    'participants.id': None,
                    'agenda.related_entities.id': None,
                    'created_at': time_param,
                    'updated_at': time_param,
                   }


class VoteList(JsonView):
    collection = db.votes
    default_fields = {'roll_call': 0, 'sources': 0}
    query_params = {'jurisdiction_id': None,
                    'date': None,
                    'passed': boolean_param,
                    'chamber': None,
                    'session': None,
                    'type': None,
                    'bill.id': None,
                    'created_at': time_param,
                    'updated_at': time_param}
