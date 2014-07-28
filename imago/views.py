from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)
from .helpers import PublicListEndpoint, PublicDetailEndpoint, get_field_list
import copy
import pytz


def dout(obj):
    """
    Helper function to ensure that we're always printing internal
    datetime objects in a fully qualified UTC timezone. This will
    let 'None' values pass through untouched.
    """
    if obj is None:
        return
    return pytz.UTC.localize(obj).isoformat()


def sfilter(obj, blacklist):
    """
    Helper function to deep copy a dict, and pop elements off.
    """
    ret = copy.deepcopy(obj)
    for el in blacklist:
        ret.pop(el)
    return ret


#
#
#
# OK. This is where we define *what* we allow to be public.
#
#
#

DIVISION_SERIALIZE = dict([
    ("id", {}),
    ("display_name", {}),
])

SOURCES_SERIALIZE = {"note": {}, "url": {},}

JURISDICTION_SERIALIZE = dict([
    ("id", {}),
    ("name", {}),
    ("url", {}),
    ("classification", {}),
    ("extras", lambda x: x.extras),
    ("feature_flags", lambda x: x.feature_flags),
    ("division", DIVISION_SERIALIZE),
])

LEGISLATIVE_SESSION_SERIALIZE = dict([
    ('identifier', {}),
    ('classification', {}),
    ('jurisdiction', JURISDICTION_SERIALIZE),
])


CONTACT_DETAIL_SERIALIZE = dict([
    ("type", {}),
    ("value", {}),
    ("note", {}),
    ("label", {}),
])


LINK_SERALIZE = dict([
    ("note", {}),
    ("url", {}),
])

IDENTIFIERS_SERIALIZE = {
    "identifier": {},
    "scheme": {},
}

OTHER_NAMES_SERIALIZE = {
    "name": {},
    "note": {},
    "start_date": {},
    "end_date": {},
}

ORGANIZATION_SERIALIZE = dict([
    ("id", {}),
    ("name", {}),
    ("image", {}),
    ("identifiers", IDENTIFIERS_SERIALIZE),
    ("links", LINK_SERALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("other_names", OTHER_NAMES_SERIALIZE),
    ("classification", {}),
    ("founding_date", {}),
    ("dissolution_date", {}),
    ("jurisdiction", JURISDICTION_SERIALIZE),
    ("sources", SOURCES_SERIALIZE),
])

ORGANIZATION_SERIALIZE['parent'] = ORGANIZATION_SERIALIZE
ORGANIZATION_SERIALIZE['children'] = sfilter(
    ORGANIZATION_SERIALIZE,
    blacklist=['parent']
)

ORGANIZATION_SERIALIZE['identifiers'] = {
    # Don't leak 'id'
    "identifier": {},
    # Don't allow recuse into our own org.
    "scheme": {},
}

PERSON_SERIALIZE = dict([
    ("id", {}),
    ("name", {}),
    ("sort_name", {}),
    ("image", {}),
    ("gender", {}),
    ("summary", {}),
    ("national_identity", {}),
    ("biography", {}),
    ("birth_date", {}),
    ("death_date", {}),

    ("identifiers", IDENTIFIERS_SERIALIZE),
    ("other_names", OTHER_NAMES_SERIALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("links", LINK_SERALIZE),
    ("sources", SOURCES_SERIALIZE),
])

POST_SERIALIZE = dict([
    ("id", {}),
    ("label", {}),
    ("role", {}),
    ("start_date", {}),
    ("end_date", {}),
    ("links", LINK_SERALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("organization", ORGANIZATION_SERIALIZE),
    ("division", DIVISION_SERIALIZE),
])

ORGANIZATION_SERIALIZE['posts'] = sfilter(
    POST_SERIALIZE,
    blacklist=["organization"]
)

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

ORGANIZATION_SERIALIZE['memberships'] = sfilter(
    # Avoid org->memberships->org loop
    MEMBERSHIP_SERIALIZE,
    blacklist=['organization']
)
ORGANIZATION_SERIALIZE['memberships']['post'] = sfilter(
    # Avoid org->memberships->post->org loop
    POST_SERIALIZE,
    blacklist=['organization']
)

PERSON_SERIALIZE['memberships'] = sfilter(
    # Avoid person->memberships->person loop
    MEMBERSHIP_SERIALIZE,
    blacklist=['person']
)

POST_SERIALIZE['memberships'] = sfilter(
    MEMBERSHIP_SERIALIZE,
    blacklist=['post']
)

LINK_BASE = dict([
    ('links', {
        'media_type': {},
        'url': {},
    }),
])

BILL_SERIALIZE = dict([
    ('id', {}),
    ('identifier', {}),
    ('legislative_session', LEGISLATIVE_SESSION_SERIALIZE),

    ('title', {}),

    ('from_organization', ORGANIZATION_SERIALIZE),

    ('classification', lambda x: x.classification),
    ('subject', lambda x: x.classification),

    ('abstracts', {
        "abstract": {},
        "note": {},
    }),

    ('other_titles', {
        "title": {},
        "note": {},
    }),

    ('other_identifiers', {
        "note": {},
        "identifier": {},
        "scheme": {},
    }),

    ('actions', {
        'organization': ORGANIZATION_SERIALIZE,
        'description': {},
        'date': {},
        'classification': lambda x: x.classification,
        'order': {},
    }),

    ('sponsorships', {
        "primary": {},
        "classification": {},
    }),

    ('documents', {
        "note": {},
        "date": {},
        "links": LINK_BASE,
    }),

    ('versions', {
        "note": {},
        "date": {},
        "links": LINK_BASE,
    }),

    ('sponsorships', {
        "primary": {},
        "classification": {},
    }),
])

VOTE_SERIALIZE = dict([
    ("id", {}),
    ("identifier", {}),
    ("motion_text", {}),
    ("motion_classification", {}),

    ('created_at', lambda x: dout(x.created_at)),
    ('updated_at', lambda x: dout(x.updated_at)),

    ('start_date', {}),
    ('end_date', {}),

    ("extras", lambda x: x.extras),
    ("motion_classification", lambda x: x.motion_classification),

    ("result", {}),
    ("organization", ORGANIZATION_SERIALIZE),
    ("legislative_session", LEGISLATIVE_SESSION_SERIALIZE),
    ("bill", BILL_SERIALIZE),
    ("counts", {
        "option": {},
        "value": {},
    }),
    ("votes", {
        "option": {},
        "voter_name": {},
        "voter": {},
        "note": {},
    }),
    ("sources", SOURCES_SERIALIZE),
])

EVENT_AGENDA_ITEM = dict([
    ('description', {}),
    ('order', {}),
    ('subjects', lambda x: x.subjects),
    ('notes', {}),

    ('related_entities', {
        "note": {},
        "entity_name": {},
        "entity_type": {},
    }),
])

EVENT_SERIALIZE = dict([
    ('id', {}),
    ('name', {}),
    ('jurisdiction', JURISDICTION_SERIALIZE),
    ('description', {}),
    ('classification', {}),

    ('start_time', lambda x: dout(x.start_time)),
    ('end_time', lambda x: dout(x.end_time)),
    ('timezone', {}),

    ('all_day', {}),
    ('status', {}),

    ('location', {
        "name": {},
        "url": {},
        "coordinates": {},  # XXX: Lambda
    }),

    ('agenda', EVENT_AGENDA_ITEM),
    ('extras', lambda x: x.extras),
])


#
#
#
# OK. This is where we define the actuall class-based views.
#
#
#


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
    default_fields = get_field_list(model, without=[
        'event_locations',
        'events',
        'organizations',
        'division',
    ]) + [
        'division.id', 'division.display_name'
    ]


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
    default_fields = get_field_list(model, without=[
        'memberships_on_behalf_of',
        'billactionrelatedentity',
        'eventrelatedentity',
        'eventparticipant',
        'billsponsorship',
        'memberships',  # Below.
        'parent_id',  # Present as parent.id
        'children',
        'actions',
        'parent',  # Below.
        'posts',
        'bills',
        'votes',
    ]) + [
        'parent.id',
        'parent.name',

        'memberships.start_date',
        'memberships.end_date',
        'memberships.person.id',
        'memberships.person.name',
        'memberships.post.id',

        'children.id',
        'children.name',

        'jurisdiction.id',
        'jurisdiction.name',
        'jurisdiction.division.id',
        'jurisdiction.division.display_name',

        'posts.id',
        'posts.label',
        'posts.role',
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
    default_fields = get_field_list(model)


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


class VoteList(PublicListEndpoint):
    model = VoteEvent
    serialize_config = VOTE_SERIALIZE
    default_fields = [
        'result', 'motion_text', 'created_at', 'start_date', 'updated_at',
        'motion_classification', 'extras',

        'counts',

        'bill.identifier', 'bill.id',
        'organization.id', 'organization.name',
    ]


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
