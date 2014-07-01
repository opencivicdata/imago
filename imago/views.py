from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)

from restless.modelviews import ListEndpoint, DetailEndpoint, Endpoint
from django.core.paginator import Paginator, EmptyPage
from restless.models import serialize
from restless.http import HttpError



class PublicListEndpoint(ListEndpoint):
    methods = ['GET']
    per_page = 100

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
            "results": [serialize(x, **self.serialize) for x in data_page.object_list]
        }



class PublicDetailEndpoint(DetailEndpoint):
    methods = ['GET']


class JurisdictionList(PublicListEndpoint):
    model = Jurisdiction


class JurisdictionDetail(PublicDetailEndpoint):
    model = Jurisdiction


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize = {
        "include": [('posts', {})]
    }


class OrganizationDetail(PublicDetailEndpoint):
    model = Jurisdiction


class PeopleList(PublicListEndpoint):
    model = Jurisdiction


class PersonDetail(PublicDetailEndpoint):
    model = Jurisdiction


class BillList(PublicListEndpoint):
    model = Jurisdiction


class BillDetail(PublicDetailEndpoint):
    model = Jurisdiction


class VoteList(PublicListEndpoint):
    model = Jurisdiction


class VoteDetail(PublicDetailEndpoint):
    model = Jurisdiction


class EventList(PublicListEndpoint):
    model = Jurisdiction


class EventDetail(PublicDetailEndpoint):
    model = Jurisdiction
