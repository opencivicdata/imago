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
#     * Neither the name of the Sunlight Foundation nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE SUNLIGHT FOUNDATION BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from opencivicdata.models import (Jurisdiction,
                                  Organization,
                                  Person,
                                  Bill,
                                  VoteEvent,
                                  Event)

from .helpers import (PublicListEndpoint,
                      PublicDetailEndpoint,
                      get_field_list)

from .serialize import (JURISDICTION_SERIALIZE,
                        ORGANIZATION_SERIALIZE,
                        PERSON_SERIALIZE,
                        VOTE_SERIALIZE,
                        BILL_SERIALIZE,
                        EVENT_SERIALIZE)
import pytz


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
        'event_locations', 'events', 'organizations', 'division',
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
        'memberships_on_behalf_of', 'billactionrelatedentity',
        'eventrelatedentity', 'eventparticipant', 'jurisdiction_id',
        'billsponsorship', 'memberships', 'parent_id', 'children', 'actions',
        'parent', 'posts', 'bills', 'votes',
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
    default_fields = get_field_list(model, without=[
        'votes',
        'billactionrelatedentity',
        'eventparticipant',
        'billsponsorship',
        'eventrelatedentity',
        'memberships',
    ]) + [
        'memberships.label',
        'memberships.role',
        'memberships.start_date',
        'memberships.end_date',
        'memberships.post.label',
        'memberships.post.role',
        'memberships.post.id',
        'memberships.post.division.id',
        'memberships.post.division.display_name',
        'memberships.organization.id',
        'memberships.organization.name',
        'memberships.organization.jurisdiction.id',
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


class VoteList(PublicListEndpoint):
    model = VoteEvent
    serialize_config = VOTE_SERIALIZE
    default_fields = [
        'result', 'motion_text', 'created_at', 'start_date', 'updated_at',
        'motion_classification', 'extras', 'id',

        'counts',

        'bill.identifier', 'bill.id',
        'organization.id', 'organization.name',
    ]


class VoteDetail(PublicDetailEndpoint):
    model = VoteEvent
    serialize_config = VOTE_SERIALIZE
    default_fields = get_field_list(model, without=[
        'eventrelatedentity',
        'legislative_session_id',
        'bill',
        'legislative_session',
        'organization',
        'organization_id',
        'bill_id',
    ]) + [
        'bill.id',
        'bill.identifier',
        'bill.legislative_session.identifier',

        'organization.id',
        'organization.name',
        'organization.classification',
    ]


class BillDetail(PublicDetailEndpoint):
    model = Bill
    serialize_config = BILL_SERIALIZE
    default_fields = get_field_list(model, without=[
        'from_organization_id',
        'eventrelatedentity',
        'related_bills_reverse',
        'legislative_session_id',
        'actions.organization',
        'votes'
    ]) + [
        'from_organization.id',
        'from_organization.name',
        'legislative_session.identifier',

        'actions.organization.id',
        'actions.organization.name',
        'actions.organization.jurisdiction.id',
        'actions.organization.jurisdiction.classification',
        'actions.organization.jurisdiction.name',
        'actions.organization.jurisdiction.division.id',
        'actions.organization.jurisdiction.division.display_name',

        'votes.result',
        'votes.motion_text',
        'votes.start_date',
        'votes.motion_classification',
        'votes.id',
        'votes.counts',
    ]


class EventList(PublicListEndpoint):
    model = Event
    serialize_config = EVENT_SERIALIZE
    default_fields = [
        'id', 'name', 'description', 'classification', 'start_time',
        'timezone', 'end_time', 'all_day', 'status',

        'agenda.description', 'agenda.order', 'agenda.subjects',
        'agenda.related_entities.note',
        'agenda.related_entities.entity_name',
        'agenda.related_entities.entity_id',
        'agenda.related_entities.entity_type',
    ]


class EventDetail(PublicDetailEndpoint):
    model = Event
    serialize_config = EVENT_SERIALIZE
    default_fields = get_field_list(model, without=[
        'location_id',
    ])
