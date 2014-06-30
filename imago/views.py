import re
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import redirect
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.core.urlresolvers import reverse
from django.db.models import Q
from .exceptions import APIError
from .utils import dict_to_mongo_query, bill_search
from .models import Division

from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)

locksmith_db = None


def _clamp(val, _min, _max):
    return _min if val < _min else _max if val > _max else val


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
        default_fields - mongodb fields parameter if not specified
            (optional - defaults to all)
        per_page
            (optional- defaults to 100)
        query_params
            (optional defaults to [])
        sort_options
        default_subfields
    """

    model = None
    default_fields = None
    per_page = 100
    query_params = {}
    sort_options = {}
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

        if isinstance(data, HttpResponse):
            return data

        data = json.dumps(
            data,
            cls=DateTimeAwareJSONEncoder,
            ensure_ascii=False
        )

        # JSONP
        cb = get_params.get('callback', None)
        if cb:
            data = '{0}({1})'.format(cb, data)

        if locksmith_db:
            locksmith_db.logs.insert({'key': request.apikey['_id'],
                                      'method': self.__class__.__name__,
                                      'query_string': request.META['QUERY_STRING'],
                                      'timestamp': datetime.datetime.utcnow()})

        return HttpResponse(data, content_type='application/json; charset=utf-8')

    def get_page(self, data, page, per_page):
        start = page * per_page
        end = start + per_page
        return data[start:end]

    def do_query(self, get_params):
        """ return data, count, extra_meta """
        fields = self.fields_from_request(get_params)
        query = self.query_from_request(get_params)
        sort = self.sort_options.get(get_params.get('sort', 'default'))
        data = self.model.objects.filter(**query)

        if sort:
            data = data.sort(**sort)

        return data, data.count(), {'django': {'sort': sort,
                                               'fields': fields,
                                               'query': query}}

    def get_data(self, get_params):
        data, total, extra_meta = self.do_query(get_params)

        try:
            per_page = _clamp(
                int(get_params.get('per_page', self.per_page)),
                1, self.per_page
            )
        except ValueError:
            per_page = self.per_page

        try:
            page = _clamp(int(get_params.get('page', 0)),
                          0, int(total / per_page))
        except ValueError:
            page = 0

        data = self.get_page(data, page, per_page)
        data = {'results': [x.to_dict() for x in data],
                'meta': {'page': page,
                         'per_page': per_page,
                         'count': len(data),
                         'total_count': total,
                         'max_page': int(total / per_page), }}

        # debug stuff into meta
        if 'debug' in get_params:
            data['meta'].update(extra_meta)

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
        return get_params


class DetailView(JsonView):
    def get_data(self, get_params, id):
        pass


class JurisdictionDetail(DetailView):
    model = Jurisdiction


class JurisdictionList(JsonView):
    model = Jurisdiction


class OrganizationDetail(DetailView):
    model = Organization


class PersonDetail(DetailView):
    model = Person


class BillDetail(DetailView):
    model = Bill


class EventDetail(DetailView):
    model = Event


class VoteDetail(DetailView):
    model = VoteEvent


class OrganizationList(JsonView):
    model = Organization


class PeopleList(JsonView):
    model = Person


class BillList(JsonView):
    model = Bill


class VoteList(JsonView):
    model = VoteEvent
