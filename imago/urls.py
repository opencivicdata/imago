from django.conf.urls import patterns
from imago.views import (JurisdictionList,
                         OrganizationList,
                         PeopleList,
                         BillList,
                         EventList,
                         VoteList,
                         JurisdictionDetail,
                         OrganizationDetail,
                         PersonDetail,
                         BillDetail,
                         EventDetail,
                         VoteDetail,
                         DivisionList,
                         DivisionDetail,
                        )

urlpatterns = patterns(
    '',
    (r'^divisions/$', DivisionList.as_view()),
    (r'^jurisdictions/$', JurisdictionList.as_view()),
    (r'^organizations/$', OrganizationList.as_view()),
    (r'^people/$', PeopleList.as_view()),
    (r'^bills/$', BillList.as_view()),
    (r'^events/$', EventList.as_view()),
    (r'^votes/$', VoteList.as_view()),

    # detail views
    (r'^(?P<id>ocd-division/.*)/$', DivisionDetail.as_view()),
    (r'^(?P<id>ocd-jurisdiction/.+)/$', JurisdictionDetail.as_view()),
    (r'^(?P<id>ocd-organization/[0-9a-f-]+)/$', OrganizationDetail.as_view()),
    (r'^(?P<id>ocd-person/[0-9a-f-]+)/$', PersonDetail.as_view()),
    (r'^(?P<id>ocd-bill/[0-9a-f-]+)/$', BillDetail.as_view()),
    (r'^(?P<id>ocd-event/[0-9a-f-]+)/$', EventDetail.as_view()),
    (r'^(?P<id>ocd-vote/[0-9a-f-]+)/$', VoteDetail.as_view()),
)
