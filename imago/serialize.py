# Copyright (c) Sunlight Foundation, 2014, under the BSD-3 License.
# Authors:
#    - Paul R. Tagliamonte <paultag@sunlightfoundation.com>

import copy
import pytz
from opencivicdata.models import Division

"""
The following specs in this file are used to limit exactly what we can
and can not show over the API.

This is primarally useful for ensuring:

     - Implementation details don't leak through (such as membership.id)

     - We can properly encode data that's getting sent out (such as
       properly encoding datetime objects)


When you add a new attribute to an object in `opencivicdata.models`, that
attribute should be added below if it's a public member of the object.
"""


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


DIVISION_SERIALIZE = dict([("id", {}), ("name", {})])
SOURCES_SERIALIZE = {"note": {}, "url": {},}

JURISDICTION_SERIALIZE = dict([
    ("id", {}),
    ("name", {}),
    ("url", {}),

    ("updated_at", {}),
    ("created_at", {}),

    ("classification", {}),
    ("extras", lambda x: x.extras),
    ("feature_flags", lambda x: x.feature_flags),

    ("division", DIVISION_SERIALIZE),
    ("division_id", {}),
])

JURISDICTION_EMBED = {
    'id': {},
    'name': {},
    'url': {},
}

LEGISLATIVE_SESSION_SERIALIZE = dict([
    ('identifier', {}),
    ('classification', {}),
    ('jurisdiction', JURISDICTION_SERIALIZE),
])

JURISDICTION_SERIALIZE['legislative_sessions'] = sfilter(
    LEGISLATIVE_SESSION_SERIALIZE,
    blacklist=['jurisdiction']
)


CONTACT_DETAIL_SERIALIZE = dict([("type", {}), ("value", {}),
                                 ("note", {}), ("label", {})])


LINK_SERIALIZE = dict([
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

    ("created_at", {}),
    ("updated_at", {}),

    ("extras", lambda x: x.extras),

    ("identifiers", IDENTIFIERS_SERIALIZE),
    ("links", LINK_SERIALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("other_names", OTHER_NAMES_SERIALIZE),
    ("classification", {}),
    ("founding_date", {}),
    ("dissolution_date", {}),
    ("jurisdiction_id", {}),
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
    ("given_name", {}),
    ("family_name", {}),
    ("sort_name", {}),
    ("image", {}),
    ("gender", {}),
    ("summary", {}),
    ("national_identity", {}),
    ("biography", {}),
    ("birth_date", {}),
    ("death_date", {}),

    ("created_at", {}),
    ("updated_at", {}),

    ("extras", lambda x: x.extras),

    ("identifiers", IDENTIFIERS_SERIALIZE),
    ("other_names", OTHER_NAMES_SERIALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("links", LINK_SERIALIZE),
    ("sources", SOURCES_SERIALIZE),
])


POST_SERIALIZE = dict([
    ("id", {}),
    ("label", {}),
    ("role", {}),
    ("start_date", {}),
    ("end_date", {}),
    ("links", LINK_SERIALIZE),
    ("contact_details", CONTACT_DETAIL_SERIALIZE),
    ("organization", ORGANIZATION_SERIALIZE),
    ("division", DIVISION_SERIALIZE),
    ("division_id", {}),
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
    "contact_details": CONTACT_DETAIL_SERIALIZE,
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


LINK_BASE = {'media_type': {}, 'url': {}}


BILL_SERIALIZE = dict([
    ('id', {}),
    ('identifier', {}),
    ('legislative_session', LEGISLATIVE_SESSION_SERIALIZE),

    ('title', {}),
    ("extras", lambda x: x.extras),

    ('from_organization', ORGANIZATION_SERIALIZE),
    ('from_organization_id', {}),

    ('created_at', lambda x: dout(x.created_at)),
    ('updated_at', lambda x: dout(x.updated_at)),

    ('classification', lambda x: x.classification),
    ('subject', lambda x: x.subject),

    ('abstracts', {"abstract": {}, "note": {}}),
    ('other_titles', {"title": {}, "note": {}}),
    ('other_identifiers', {"note": {}, "identifier": {}, "scheme": {}}),

    ('related_bills', {"identifier": {},
                       "legislative_session": LEGISLATIVE_SESSION_SERIALIZE,
                       "relation_type": {}}),

    ('actions', {'organization': ORGANIZATION_SERIALIZE, 'description': {},
                 'date': {}, 'classification': lambda x: x.classification,
                 'order': {}, 
                 'related_entities' : {'name' : {}, 'entity_type' : {},
                                       'organization_id' : {}, 
                                       'person_id' : {}}}),

    ('sponsorships', {"primary": {}, "classification": {}, "entity_name": {},
                      "entity_type": {}, "entity_id": {}}),
    ('documents', {"note": {}, "date": {}, "links": LINK_BASE}),
    ('versions', {"note": {}, "date": {}, "links": LINK_BASE}),

    ("sources", SOURCES_SERIALIZE),
])


BILL_SERIALIZE['related_bills']['bill'] = BILL_SERIALIZE


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

    ("result", {}),
    ("legislative_session", LEGISLATIVE_SESSION_SERIALIZE),

    ('organization_id', {}),
    ("organization", ORGANIZATION_SERIALIZE),

    ('bill_id', {}),
    ("bill", BILL_SERIALIZE),
    ("counts", {"option": {}, "value": {}}),
    ("votes", {"option": {}, "voter_name": {}, "voter": {}, "note": {}}),
    ("sources", SOURCES_SERIALIZE),
])


BILL_SERIALIZE['votes'] = sfilter(
    VOTE_SERIALIZE,
    blacklist=['bill'],
)


EVENT_AGENDA_ITEM = dict([
    ('description', {}),
    ('order', {}),
    ('subjects', lambda x: x.subjects),
    ('notes', {}),

    ('related_entities', {"note": {}, "entity_name": {}, "entity_type": {},
                          "entity_id": {}}),
])


EVENT_SERIALIZE = dict([
    ('id', {}),
    ('name', {}),
    ('jurisdiction', JURISDICTION_EMBED),
    ('jurisdiction_id', {}),
    ('description', {}),
    ('classification', {}),

    ('participants', {'note': {}, "entity_name": {}, "entity_type": {},
                      "entity_id": {}}),

    ('documents', {"note": {}, "date": {}, "links": LINK_BASE}),
    ('media', {"note": {}, "date": {}, "offset": {}, "links": LINK_BASE}),

    ("links", LINK_SERIALIZE),

    ('created_at', {}),
    ('updated_at', {}),

    ('start_time', lambda x: dout(x.start_time)),
    ('end_time', lambda x: dout(x.end_time)),
    ('timezone', {}),

    ('all_day', {}),
    ('status', {}),

    ('location', {"name": {}, "url": {}, "coordinates": {}}),

    ('agenda', EVENT_AGENDA_ITEM),
    ('extras', lambda x: x.extras),

    ("sources", SOURCES_SERIALIZE),
])

def boundary_to_dict(boundary):
    d = boundary.as_dict()
    d['boundary_set'] = {'start_date': boundary.set.start_date,
                         'end_date': boundary.set.end_date,
                         'name': boundary.set.name}
    return d


DIVISION_SERIALIZE = {
    'id': {},
    'name': {},
    'country': {},
    'jurisdictions': JURISDICTION_SERIALIZE,
    'children': lambda division: [{'id': d.id, 'name': d.name}
                                   for d in Division.objects.children_of(division.id)],
    'geometries': lambda division: [boundary_to_dict(dg.boundary)
                                    for dg in division.geometries.all()],
    'posts' : POST_SERIALIZE
}
