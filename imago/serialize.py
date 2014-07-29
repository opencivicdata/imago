# Copyright (c) Sunlight Foundation, 2014
# Authors:
#    - Paul R. Tagliamonte <paultag@sunlightfoundation.com>
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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


DIVISION_SERIALIZE = dict([
    ("id", {}),
    ("display_name", {}),
])

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

LEGISLATIVE_SESSION_SERIALIZE = dict([
    ('identifier', {}),
    ('classification', {}),
    ('jurisdiction', JURISDICTION_SERIALIZE),
])

JURISDICTION_SERIALIZE['legislative_sessions'] = sfilter(
    LEGISLATIVE_SESSION_SERIALIZE,
    blacklist=['jurisdiction']
)


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

    ("created_at", {}),
    ("updated_at", {}),

    ("extras", lambda x: x.extras),

    ("identifiers", IDENTIFIERS_SERIALIZE),
    ("links", LINK_SERALIZE),
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

LINK_BASE = {
    'media_type': {},
    'url': {},
}

BILL_SERIALIZE = dict([
    ('id', {}),
    ('identifier', {}),
    ('legislative_session', LEGISLATIVE_SESSION_SERIALIZE),
    ('legislative_session_id', {}),

    ('title', {}),
    ("extras", lambda x: x.extras),

    ('from_organization', ORGANIZATION_SERIALIZE),
    ('from_organization_id', {}),

    ('created_at', lambda x: dout(x.created_at)),
    ('updated_at', lambda x: dout(x.updated_at)),

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

    ('related_bills', {
        "identifier": {},
        "legislative_session": LEGISLATIVE_SESSION_SERIALIZE,
        "relation_type": {},
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
        "entity_name": {},
        "entity_type": {},
        "entity_id": {},
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


BILL_SERIALIZE['votes'] = sfilter(
    VOTE_SERIALIZE,
    blacklist=['bill'],
)

EVENT_AGENDA_ITEM = dict([
    ('description', {}),
    ('order', {}),
    ('subjects', lambda x: x.subjects),
    ('notes', {}),

    ('related_entities', {
        "note": {},
        "entity_name": {},
        "entity_type": {},
        "entity_id": {},
    }),
])

EVENT_SERIALIZE = dict([
    ('id', {}),
    ('name', {}),
    ('jurisdiction', JURISDICTION_SERIALIZE),
    ('jurisdiction_id', {}),
    ('description', {}),
    ('classification', {}),

    ('participants', {
        'note': {},
        "entity_name": {},
        "entity_type": {},
        "entity_id": {},
    }),

    ('documents', {
        "note": {},
        "date": {},
        "links": LINK_BASE,
    }),

    ('media', {
        "note": {},
        "date": {},
        "offset": {},
        "links": LINK_SERALIZE,
    }),

    ("links", LINK_SERALIZE),

    ('created_at', {}),
    ('updated_at', {}),

    ('start_time', lambda x: dout(x.start_time)),
    ('end_time', lambda x: dout(x.end_time)),
    ('timezone', {}),

    ('all_day', {}),
    ('status', {}),

    ('location', {
        "name": {},
        "url": {},
    }),

    ('agenda', EVENT_AGENDA_ITEM),
    ('extras', lambda x: x.extras),

    ("sources", SOURCES_SERIALIZE),
])


