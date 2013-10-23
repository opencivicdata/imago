import re
import json
import datetime
from tarfile import TarFile  # For tar view
import pymongo
from django.http import HttpResponse
from django.conf import settings
from django.core.serializers.json import DateTimeAwareJSONEncoder
from .core import db
from .exceptions import APIError
from .utils import dict_to_mongo_query, bill_search
from django.views.generic import View


from tarfile import TarFile, TarInfo
from cStringIO import StringIO
from contextlib import contextmanager

if getattr(settings, 'USE_LOCKSMITH', False):
    from locksmith.mongoauth.db import db as locksmith_db
else:
    locksmith_db = None


@contextmanager
def buffer():
    s = StringIO()
    try:
        yield s
    except:
        s.close()
        raise


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


class TarballDumpView(View):

    @staticmethod
    def generate_tarball(data):
        with buffer() as output:
            tf = TarFile(fileobj=output, mode='w')
            for path, datum in data:
                with buffer() as string:
                    json.dump(datum, string, cls=DateTimeAwareJSONEncoder)
                    info = TarInfo(name=path)
                    info.size = string.tell()
                    string.seek(0)
                    tf.addfile(tarinfo=info, fileobj=string)
            output.seek(0)
            return output.getvalue()

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()

        try:
            if locksmith_db and (not hasattr(request, 'apikey') or
                                 request.apikey['status'] != 'A'):
                raise APIError('Authorization Required: obtain API key at ' +
                               settings.LOCKSMITH_REGISTRATION_URL, status=401)
            data = self.get_data(get_params, *args, **kwargs)
        except APIError as e:
            resp = {'error': str(e)}
            data = json.dumps(resp)
            return HttpResponse(data, status=e.status)

        # verify data is a [('filename', {}), ...]
        data = TarballDumpView.generate_tarball(data)

        if locksmith_db:
            locksmith_db.logs.insert({'key': request.apikey['_id'],
                                      'method': self.__class__.__name__,
                                      'query_string': request.META['QUERY_STRING'],
                                      'timestamp': datetime.datetime.utcnow()})

        return HttpResponse(data)

    def get_data(self, id, get_params):
        return NotImplemented


class JurisdictionDumpView(TarballDumpView):
    def get_data(self, get_params, id):
        spec = {"jurisdiction_id": id}

        meta = db.jurisdictions.find_one({"_id": id})
        if meta is None:
            return

        for x in [
            'latest_json_url', 'latest_csv_url',
            'latest_json_date', 'latest_csv_date'
        ]:
            if x in meta:
                meta.pop(x)

        for key in meta.keys():
            if key.startswith("_") and key != "_id":
                meta.pop(key)

        yield ("{jurisdiction}/jurisdiction.json".format(
            jurisdiction=meta['_id']
        ), meta)

        for collection in [
            db.bills,
            db.votes,
            db.events,
            db.organizations,
        ]:
            for entry in collection.find(spec, timeout=False):
                yield ("{jurisdiction}/{id}".format(
                    jurisdiction=entry['jurisdiction_id'],
                    id=entry['_id']
                ), entry)

        for orga in db.organizations.find({"jurisdiction_id": meta['_id'],
                                           "classification": "legislature"}):

            for membership in db.memberships.find({
                "organization_id": orga['_id']
            }, timeout=False):
                person = db.people.find_one({"_id": membership['person_id']})

                data = list(db.memberships.find({  # XXX: Ugh...
                    "person_id": person['_id']
                }, timeout=False))

                for datum in data:
                    datum.pop('_id')

                person['memberships'] = data

                yield ("{jurisdiction}/{id}".format(
                    jurisdiction=meta['_id'],
                    id=person['_id']
                ), person)


class JsonView(View):
    """ Base view for writing API views

    Properties to set:
        collection - collection to query
        default_fields - mongodb fields parameter if not specified
            (optional - defaults to all)
        per_page
            (optional- defaults to 100)
        query_params
            (optional defaults to [])
        sort_options
        default_subfields
    """

    default_fields = None
    per_page = 100
    query_params = {}
    sort_options = {
        'default': [('created_at', pymongo.DESCENDING)],
        'created_at': [('created_at', pymongo.DESCENDING)],
        'updated_at': [('updated_at', pymongo.DESCENDING)]
    }
    default_subfields = None

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()

        try:
            if locksmith_db and (not hasattr(request, 'apikey') or
                                 request.apikey['status'] != 'A'):
                raise APIError('Authorization Required: obtain API key at ' +
                               settings.LOCKSMITH_REGISTRATION_URL, status=401)
            data = self.get_data(get_params, *args, **kwargs)
        except APIError as e:
            resp = {'error': str(e)}
            data = json.dumps(resp)
            return HttpResponse(data, status=e.status)

        data = json.dumps(self._clean(data), cls=DateTimeAwareJSONEncoder,
                          ensure_ascii=False)

        # JSONP
        cb = get_params.get('callback', None)
        if cb:
            data = '{0}({1})'.format(cb, data)

        if locksmith_db:
            locksmith_db.logs.insert({'key': request.apikey['_id'],
                                      'method': self.__class__.__name__,
                                      'query_string': request.META['QUERY_STRING'],
                                      'timestamp': datetime.datetime.utcnow()})

        return HttpResponse(data)

    def get_data(self, get_params):
        fields = self.fields_from_request(get_params)
        query = self.query_from_request(get_params)
        sort = self.sort_options.get(get_params.get('sort', 'default'))
        data = self.collection.find(query, fields=fields)
        if sort:
            data = data.sort(sort)

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
                          0, total / per_page)
        except ValueError:
            page = 0

        data = list(data.skip(page * per_page).limit(per_page))
        data = {'results': data, 'meta': {'page': page,
                                          'per_page': per_page,
                                          'count': len(data),
                                          'total_count': total,
                                          'max_page': total/per_page,
                                         }
               }

        # debug stuff into meta
        debug = 'debug' in get_params
        if debug:
            data['meta']['mongo'] = {'sort': sort, 'fields': fields,
                                     'query': query}

        return data

    def fields_from_request(self, get_params):
        fields = get_params.get('fields', None)

        if not fields:
            return self.default_fields
        else:
            d = {field: 1 for field in fields.split(',')}
            d['_id'] = d.pop('id', 1)
            d['_type'] = 1
            return d

    def query_from_request(self, get_params):
        return dict_to_mongo_query(get_params, self.query_params)

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

    def get_data(self, get_params, id):
        fields = self.fields_from_request(get_params)
        result = self.collection.find_one({'_id': id}, fields=fields)

        if not result:
            raise APIError('no such object: ' + id, 404)

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
    sort_options = {
        'default': [('name', pymongo.ASCENDING)]
    }


class OrganizationList(JsonView):
    collection = db.organizations
    default_fields = {'contact_details': 0, 'sources': 0, 'posts': 0,
                      'founding_date': 0, 'dissolution_date': 0}
    query_params = {'classification': None,
                    'founding_date': None,
                    'dissolution_date': None,
                    'jurisdiction_id': None,
                    'parent_id': None,
                    'division_id': None,
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
                    'updated_at': time_param,
                    'district': None,
                    # member_of
                    # ever_member_of
                   }

    def query_from_request(self, get_params):
        query = super(PeopleList, self).query_from_request(get_params)
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
                      'summaries': 0, 'other_titles': 0, 'documents': 0
                     }
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
    # TODO: title search, search_window

    def get_data(self, get_params):
        fields = self.fields_from_request(get_params)
        sort = get_params.get('sort', 'default')
        bill_results = bill_search(get_params, self.query_params, fields, sort)

        total = len(bill_results)

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

        data = list(bill_results[page*per_page:page*per_page+per_page])
        data = {'results': data, 'meta': {'page': page,
                                          'per_page': per_page,
                                          'count': len(data),
                                          'total_count': total,
                                          'max_page': total/per_page,
                                         }
               }

        # debug stuff into meta
        debug = 'debug' in get_params
        if debug:
            data['meta']['mongo'] = {'sort': sort, 'fields': fields,
                                     'query': bill_results.mongo_query}
            data['meta']['elasticsearch'] = bill_results.es_search

        return data


class EventList(JsonView):
    collection = db.events
    default_fields = {'sources': 0}
    query_params = {'jurisdiction_id': None,
                    'participants.id': None,
                    'agenda.related_entities.id': None,
                    'when': time_param,
                    'created_at': time_param,
                    'updated_at': time_param,
                   }
    sort_options = {
        'default': [('created_at', pymongo.DESCENDING)],
        'created_at': [('created_at', pymongo.DESCENDING)],
        'updated_at': [('updated_at', pymongo.DESCENDING)],
        'when': [('when', pymongo.DESCENDING)],
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
    sort_options = {
        'default': [('created_at', pymongo.DESCENDING)],
        'created_at': [('created_at', pymongo.DESCENDING)],
        'updated_at': [('updated_at', pymongo.DESCENDING)],
        'date': [('date', pymongo.DESCENDING)],
    }
