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
ORGANIZATION_SERIALIZE = defaultdict(dict)
PERSON_SERIALIZE = defaultdict(dict)
BILL_SERIALIZE = defaultdict(dict)
VOTE_SERIALIZE = defaultdict(dict)
EVENT_SERIALIZE = defaultdict(dict)


class JurisdictionList(PublicListEndpoint):
    model = Jurisdiction
    serialize_config = JURISDICTION_SERIALIZE
    default_fields = ['name', 'extras']

    def adjust_filters(self, params):
        if 'name' in params:
            params['name__icontains'] = params.pop('name')
        return params


class JurisdictionDetail(PublicDetailEndpoint):
    model = Jurisdiction
    serialize_config = JurisdictionList.serialize_config
    default_fields = []


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize_config = {}
    default_fields = serialize_config.keys()


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
