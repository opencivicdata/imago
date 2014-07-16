from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)
from .helpers import PublicListEndpoint, PublicDetailEndpoint, get_field_list
from collections import defaultdict


DIVISION_SERIALIZE = defaultdict(dict)
JURISDICTION_SERIALIZE = defaultdict(dict, [
    ("extras", lambda x: x.extras),
    ("feature_flags", lambda x: x.feature_flags),
    ("division", DIVISION_SERIALIZE),
])

LEGISLATIVE_SESSION_SERIALIZE = defaultdict(dict, [
    ('jurisdiction', JURISDICTION_SERIALIZE),
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

LINK_BASE = defaultdict(dict, [
    ('links', {
        'media_type': {},
        'url': {},
    }),
])

BILL_SERIALIZE = defaultdict(dict, [
    ('legislative_session', LEGISLATIVE_SESSION_SERIALIZE),
    ('from_organization', ORGANIZATION_SERIALIZE),
    ('classification', lambda x: x.classification),
    ('subject', lambda x: x.classification),
    ('actions', {
        'organization': ORGANIZATION_SERIALIZE,
        'classification': lambda x: x.classification,
    }),
    ('documents', {
        "note": {}, "date": {}, "links": LINK_BASE,
    }),
    ('versions', {
        "note": {}, "date": {}, "links": LINK_BASE,
    }),
    ('abstracts', defaultdict(dict)),
    ('other_titles', defaultdict(dict)),
    ('other_identifiers', defaultdict(dict)),
    ('sponsorships', {"primary": {}, "classification": {}}),
])

VOTE_SERIALIZE = defaultdict(dict, [
])

EVENT_AGENDA_ITEM = defaultdict(dict, [
    ('subjects', lambda x: x.subjects),
    ('related_entities', defaultdict(dict)),
])

EVENT_SERIALIZE = defaultdict(dict, [
    ('jurisdiction', JURISDICTION_SERIALIZE),
    ('agenda', EVENT_AGENDA_ITEM),
    ('extras', lambda x: x.extras),
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
    # default_fields = JurisdictionList.default_fields
    default_fields = get_field_list(model)


class OrganizationList(PublicListEndpoint):
    model = Organization
    serialize_config = ORGANIZATION_SERIALIZE
    default_fields = ['id', 'name', 'image', 'classification',
                      'jurisdiction.id', 'parent.id', 'parent.name',
                      'memberships.person.id', 'memberships.person.name',
                      'memberships.post.id', 'memberships.post.label',
                      'memberships.post.role',]


class OrganizationDetail(PublicDetailEndpoint):
    model = Organization
    serialize_config = ORGANIZATION_SERIALIZE
    default_fields = [
        'created_at', 'updated_at', 'extras', 'id', 'name', 'image',
        'classification', 'founding_date', 'dissolution_date',

        'parent.id',
        'parent.name',

        'jurisdiction.id',
        'jurisdiction.name',
        'jurisdiction.division.id',
        'jurisdiction.division.display_name',

        'posts.id',
        'posts.label',
        'posts.role',

        'memberships.person.id',
        'memberships.person.name',
        'memberships.post.id',
        'memberships.post.label',
        'memberships.post.role',

        'sources',
    ]



class PeopleList(PublicListEndpoint):
    model = Person
    serialize_config = PERSON_SERIALIZE
    default_fields = [
        'name', 'id', 'sort_name', 'image', 'gender',

        'memberships.organization.id',
        'memberships.organization.name',
        'memberships.organization.classification',
        'memberships.organization.jurisdiction.id',
        'memberships.organization.jurisdiction.name',

        'memberships.post.id',
        'memberships.post.label',
        'memberships.post.role',
    ]


class PersonDetail(PublicDetailEndpoint):
    model = Person
    serialize_config = PERSON_SERIALIZE
    default_fields = [
        'id', 'name', 'sort_name', 'image', 'gender', 'summary',
        'national_identity', 'biography', 'birth_date', 'death_date',

        'memberships.organization.id',
        'memberships.organization.name',
        'memberships.organization.classification',

        'memberships.organization.jurisdiction.id',
        'memberships.organization.jurisdiction.name',

        'memberships.organization.jurisdiction.division.id',
        'memberships.organization.jurisdiction.division.display_name',

        'memberships.post.id',
        'memberships.post.label',
        'memberships.post.role',
    ]


class BillList(PublicListEndpoint):
    model = Bill
    serialize_config = BILL_SERIALIZE
    default_fields = [
        'id', 'identifier', 'title', 'classification',

        'from_organization.name',
        'from_organization.id',

        'from_organization.jurisdiction.id',
        'from_organization.jurisdiction.name',
    ]


class BillDetail(PublicDetailEndpoint):
    model = Bill
    serialize_config = BILL_SERIALIZE
    default_fields = get_field_list(model)
    # default_fields = [
    #     'id', 'identifier', 'title', 'classification', 'abstracts',

    #     'other_titles.title',
    #     'other_titles.note',

    #     'from_organization.name',
    #     'from_organization.id',

    #     'from_organization.jurisdiction.id',
    #     'from_organization.jurisdiction.name',

    #     'documents.note',
    #     'documents.date',
    #     'documents.links.url',
    #     'documents.links.media_type',

    #     'versions.note',
    #     'versions.date',
    #     'versions.links.url',
    #     'versions.links.media_type',
    # ]


class VoteList(PublicListEndpoint):
    model = VoteEvent
    serialize_config = VOTE_SERIALIZE
    default_fields = []


class VoteDetail(PublicDetailEndpoint):
    model = VoteEvent
    serialize_config = VOTE_SERIALIZE
    default_fields = get_field_list(model)


class EventList(PublicListEndpoint):
    model = Event
    serialize_config = EVENT_SERIALIZE
    default_fields = [
        'id', 'name', 'description', 'classification', 'start_time',
        'timezone', 'end_time', 'all_day', 'status',

        'agenda.description', 'agenda.order', 'agenda.subjects',
        'agenda.related_entities.note',
        'agenda.related_entities.entity_name',
    ]


class EventDetail(PublicDetailEndpoint):
    model = Event
    serialize_config = EVENT_SERIALIZE
    default_fields = get_field_list(model)
