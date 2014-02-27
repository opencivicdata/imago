from django.conf.urls import patterns, url
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
    url(r'^divisions/$', DivisionList.as_view()),
    url(r'^jurisdictions/$', JurisdictionList.as_view()),
    url(r'^organizations/$', OrganizationList.as_view()),
    url(r'^people/$', PeopleList.as_view()),
    url(r'^bills/$', BillList.as_view()),
    url(r'^events/$', EventList.as_view()),
    url(r'^votes/$', VoteList.as_view()),

    # detail views
    url(r'^(?P<id>ocd-division/.*)/$', DivisionDetail.as_view(), name='division'),
    url(r'^(?P<id>ocd-jurisdiction/.+)/$', JurisdictionDetail.as_view()),
    url(r'^(?P<id>ocd-organization/[0-9a-f-]+)/$', OrganizationDetail.as_view()),
    url(r'^(?P<id>ocd-person/[0-9a-f-]+)/$', PersonDetail.as_view()),
    url(r'^(?P<id>ocd-bill/[0-9a-f-]+)/$', BillDetail.as_view()),
    url(r'^(?P<id>ocd-event/[0-9a-f-]+)/$', EventDetail.as_view()),
    url(r'^(?P<id>ocd-vote/[0-9a-f-]+)/$', VoteDetail.as_view()),
)
