# Copyright (c) Sunlight Foundation, 2014, under the BSD-3 License.
# Authors:
#    - Paul R. Tagliamonte <paultag@sunlightfoundation.com>


from opencivicdata.models import (Jurisdiction,
                                  Organization,
                                  Person,
                                  Bill,
                                  VoteEvent,
                                  Event,
                                  Division
                                 )

from .helpers import (PublicListEndpoint,
                      PublicDetailEndpoint,
                      get_field_list)

from .serialize import (JURISDICTION_SERIALIZE,
                        ORGANIZATION_SERIALIZE,
                        PERSON_SERIALIZE,
                        VOTE_SERIALIZE,
                        BILL_SERIALIZE,
                        EVENT_SERIALIZE)
from restless.http import HttpError

"""
This module contains the class-based views that we expose over the API.

The common logic for these views are in imago.helpers.*Endpoint
"""


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


class DivisionList(PublicListEndpoint):
    model = Division
    serialize_config = {'id': {}, 'name': {}, 'country': {}}
    default_fields = ['id', 'name', 'country']

    def adjust_filters(self, params):
        lat = params.pop('lat', None)
        lon = params.pop('lon', None)
        if lat and lon:
            params['geometries__boundary__shape__contains'] = 'POINT({} {})'.format(lon, lat)
        elif lat or lon:
            raise HttpError(400, "must specify lat & lon together")
        return params
