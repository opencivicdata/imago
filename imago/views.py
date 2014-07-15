from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)
from .helpers import PublicListEndpoint, PublicDetailEndpoint
from collections import defaultdict


DIVISION_SERIALIZE = defaultdict(dict)
JURISDICTION_SERIALIZE = defaultdict(dict, [
    ("extras", lambda x: x.extras),
    ("feature_flags", lambda x: x.feature_flags),
    ("division", DIVISION_SERIALIZE),
])

ORGANIZATION_SERIALIZE = defaultdict(dict, [
    ("jurisdiction", JURISDICTION_SERIALIZE),
])
ORGANIZATION_SERIALIZE['parent'] = ORGANIZATION_SERIALIZE

PERSON_SERIALIZE = defaultdict(dict, [
])

POST_SERIALIZE = defaultdict(dict, [
    ("organization", ORGANIZATION_SERIALIZE),
    ("division", DIVISION_SERIALIZE),
])

ORGANIZATION_SERIALIZE['posts'] = POST_SERIALIZE

MEMBERSHIP_SERIALIZE = {
    # Explicit to avoid letting `id' leak out.
    "start_date": {},
    "end_date": {},
    "role": {},
    "label": {},
    "organization": ORGANIZATION_SERIALIZE,
    "person": PERSON_SERIALIZE,
    "post": POST_SERIALIZE,
    "on_behalf_of": ORGANIZATION_SERIALIZE,
}

ORGANIZATION_SERIALIZE['memberships'] = MEMBERSHIP_SERIALIZE
PERSON_SERIALIZE['memberships'] = MEMBERSHIP_SERIALIZE
POST_SERIALIZE['memberships'] = MEMBERSHIP_SERIALIZE


BILL_SERIALIZE = defaultdict(dict, [
])

VOTE_SERIALIZE = defaultdict(dict, [
])

EVENT_SERIALIZE = defaultdict(dict, [
])


class JurisdictionList(PublicListEndpoint):
    model = Jurisdiction
    serialize_config = JURISDICTION_SERIALIZE
    default_fields = ['id', 'name', 'url', 'classification', 'feature_flags',
                      'division.id', 'division.display_name']

    def adjust_filters(self, params):
        if 'name' in params:
            params['name__icontains'] = params.pop('name')
        return params


class JurisdictionDetail(PublicDetailEndpoint):
    model = Jurisdiction
    serialize_config = JURISDICTION_SERIALIZE
    default_fields = JurisdictionList.default_fields


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize_config = ORGANIZATION_SERIALIZE
    default_fields = ['id', 'name', 'image', 'classification',
                      'jurisdiction.id',
                      'parent.id', 'parent.name',

                      'memberships.person.id', 'memberships.person.name',
                      'memberships.post.id', 'memberships.post.label', 'memberships.post.role',
                     ]


class OrganizationDetail(PublicDetailEndpoint):
    model = Organization
    serialize_config = OrganizationList.serialize_config
    default_fields = OrganizationList.default_fields


class PeopleList(PublicListEndpoint):
    model = Person
    serialize_config = {
    }
    default_fields = []


class PersonDetail(PublicDetailEndpoint):
    model = Person
    serialize_config = {}
    default_fields = []


class BillList(PublicListEndpoint):
    model = Bill
    serialize_config = {}
    default_fields = []


class BillDetail(PublicDetailEndpoint):
    model = Bill
    serialize_config = {}
    default_fields = []


class VoteList(PublicListEndpoint):
    model = VoteEvent
    default_fields = []


class VoteDetail(PublicDetailEndpoint):
    model = VoteEvent
    default_fields = []


class EventList(PublicListEndpoint):
    model = Event
    default_fields = []


class EventDetail(PublicDetailEndpoint):
    model = Event
    default_fields = []
