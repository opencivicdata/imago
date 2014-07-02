from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)

from restless.modelviews import ListEndpoint, DetailEndpoint, Endpoint
from django.core.paginator import Paginator, EmptyPage
from restless.models import serialize
from restless.http import HttpError


def imagoserialize(obj, *args, rawfields=None, **kwargs):

    if 'include' not in kwargs:
        kwargs['include'] = []

    raw = rawfields if rawfields is not None else []

    for key in raw:
        kwargs['include'].append((key, lambda x: getattr(x, key)))

    return serialize(obj, *args, **kwargs)


class PublicListEndpoint(ListEndpoint):
    methods = ['GET']
    per_page = 100
    serialize_config = {}
    serialize_raw = []

    def filter(self, data, **kwargs):
        return data

    def sort(self, data, **kwargs):
        return data

    def paginate(self, data, page):
        paginator = Paginator(data, per_page=self.per_page)
        return paginator.page(page)

    def get(self, request, *args, **kwargs):
        params = request.params
        page = 1
        if 'page' in params:
            page = int(params.pop('page'))

        sort_by = []
        if 'sort_by' in params:
            sort_by = params.pop('sort_by').split(",")

        data = self.get_query_set(request, *args, **kwargs)
        data = self.filter(data, **params)
        data = self.sort(data)
        try:
            data_page = self.paginate(data, page)
        except EmptyPage:
            raise HttpError(
                404,
                'No such page (heh, literally - its out of bounds)'
            )

        return {
            "meta": {
                "count": data.count(),
                "pages": data_page.end_index(),
                "cur_page": page,
                "per_page": self.per_page,
            },
            "results": [
                imagoserialize(x, rawfields=self.serialize_raw, **self.serialize_config)
                for x in data_page.object_list
            ]
        }



class PublicDetailEndpoint(DetailEndpoint):
    methods = ['GET']


class JurisdictionList(PublicListEndpoint):
    model = Jurisdiction


class JurisdictionDetail(PublicDetailEndpoint):
    model = Jurisdiction


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize_config = {"include": [('posts', {})]}


class OrganizationDetail(PublicDetailEndpoint):
    model = Organization


class PeopleList(PublicListEndpoint):
    model = Person
    serialize_config = {"include": [
        ('memberships', {
            "include": [
                ('post', {})
            ]
        }),
    ]}


class PersonDetail(PublicDetailEndpoint):
    model = Person


class BillList(PublicListEndpoint):
    model = Bill
    serialize_raw = ['extras', 'classification', 'subject',]


class BillDetail(PublicDetailEndpoint):
    model = Bill


class VoteList(PublicListEndpoint):
    model = VoteEvent


class VoteDetail(PublicDetailEndpoint):
    model = VoteEvent


class EventList(PublicListEndpoint):
    model = Event


class EventDetail(PublicDetailEndpoint):
    model = Event
