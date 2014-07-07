from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)

from restless.modelviews import ListEndpoint, DetailEndpoint, Endpoint
from django.core.paginator import Paginator, EmptyPage
from restless.models import serialize
from restless.http import HttpError


def smerge(dict1, dict2):
    ret = dict(dict1)
    for k, v in dict2.items():
        if k not in ret:
            ret[k] = []
        rk = list(ret[k])
        rk += v
        ret[k] = rk
    return ret



POST_SERIALIZE = {
    "include": [
        ('extras', lambda x: x.extras),
    ],
    "exclude": [
        'organization',
    ]
}


ORGANIZATION_SERIALIZE = {
    "include": [
        ('posts', POST_SERIALIZE),
        ('jurisdiction', {
            "fields": [
                "id", "name", "division_id"
            ]
        }),
    ]
}


MEMBERSHIP_SERIALIZE = {
    "include": [
        ('organization', {
            "fields": ["id", "name", "classification"]
        }),
        ('extras', lambda x: x.extras),
        ('post', smerge(
            POST_SERIALIZE,
            {"include": [
                ('organization', {
                    "fields": [
                        "id",
                        "id", "name", "classification"
                    ]
                })
            ]}
        )),
    ],
    "exclude": ['id']
}


PERSON_SERIALIZE = {"include": [
    ('extras', lambda x: x.extras),
    ('memberships', smerge(MEMBERSHIP_SERIALIZE, {
        "exclude": ["person"],
    })),
]}


BILL_SERIALIZE = {
    "include": [
        ('extras', lambda x: x.extras),
        ('subject', lambda x: x.subject),
        ('classification', lambda x: x.classification),
        ('legislative_session', lambda x: x.legislative_session.name),
    ]
}


JURISDICTION_SERIALIZE = {
    "include": [
        ('extras', lambda x: x.extras),
        ('feature_flags', lambda x: x.feature_flags),
    ]
}


class PublicListEndpoint(ListEndpoint):
    methods = ['GET']
    per_page = 100
    serialize_config = {}

    def filter(self, data, **kwargs):
        return data.filter(**kwargs)

    def sort(self, data, sort_by):
        return data.order_by(*sort_by)

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
        data = self.sort(data, sort_by)
        try:
            data_page = self.paginate(data, page)
        except EmptyPage:
            raise HttpError(
                404,
                'No such page (heh, literally - its out of bounds)'
            )

        return {
            "meta": {
                "count": len(data_page.object_list),
                "page": page,
                "per_page": self.per_page,
                "max_page": data_page.end_index(),
                "total_count": data.count(),
            },
            "results": [
                serialize(x, **self.serialize_config)
                for x in data_page.object_list
            ]
        }


class PublicDetailEndpoint(DetailEndpoint):
    methods = ['GET']


class JurisdictionList(PublicListEndpoint):
    model = Jurisdiction
    serialize_config = JURISDICTION_SERIALIZE


class JurisdictionDetail(PublicDetailEndpoint):
    model = Jurisdiction
    serialize_config = JURISDICTION_SERIALIZE


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize_config = ORGANIZATION_SERIALIZE


class OrganizationDetail(PublicDetailEndpoint):
    model = Organization
    serialize_config = ORGANIZATION_SERIALIZE


class PeopleList(PublicListEndpoint):
    model = Person
    serialize_config = PERSON_SERIALIZE


class PersonDetail(PublicDetailEndpoint):
    model = Person
    serialize_config = PERSON_SERIALIZE


class BillList(PublicListEndpoint):
    model = Bill
    serialize_config = BILL_SERIALIZE


class BillDetail(PublicDetailEndpoint):
    model = Bill
    serialize_config = BILL_SERIALIZE


class VoteList(PublicListEndpoint):
    model = VoteEvent


class VoteDetail(PublicDetailEndpoint):
    model = VoteEvent


class EventList(PublicListEndpoint):
    model = Event


class EventDetail(PublicDetailEndpoint):
    model = Event
