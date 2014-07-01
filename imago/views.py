from opencivicdata.models import (Jurisdiction, Organization, Person,
                                  Bill, VoteEvent, Event)

from restless.modelviews import ListEndpoint, DetailEndpoint


class JurisdictionList(ListEndpoint):
    model = Jurisdiction


class JurisdictionDetail(DetailEndpoint):
    model = Jurisdiction


class OrganizationList(ListEndpoint):
    model = Jurisdiction


class OrganizationDetail(DetailEndpoint):
    model = Jurisdiction


class PeopleList(ListEndpoint):
    model = Jurisdiction


class PersonDetail(DetailEndpoint):
    model = Jurisdiction


class BillList(ListEndpoint):
    model = Jurisdiction


class BillDetail(DetailEndpoint):
    model = Jurisdiction


class VoteList(ListEndpoint):
    model = Jurisdiction


class VoteDetail(DetailEndpoint):
    model = Jurisdiction


class EventList(ListEndpoint):
    model = Jurisdiction


class EventDetail(DetailEndpoint):
    model = Jurisdiction
