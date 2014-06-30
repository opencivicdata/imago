from django.conf.urls import patterns, url
from imago.views import (JurisdictionList,
                         PeopleList,
                         VoteList,
                         EventList,
                         OrganizationList,

                         JurisdictionDetail,
                         PersonDetail,
                         EventDetail,
                         VoteDetail,
                         OrganizationDetail,)

urlpatterns = patterns(
    '',
    url(r'^jurisdictions/$', JurisdictionList.as_view()),
    url(r'^people/$', PeopleList.as_view()),
    url(r'^votes/$', VoteList.as_view()),
    url(r'^events/$', EventList.as_view()),
    url(r'^organizations/$', OrganizationList.as_view()),

    # detail views
    url(r'^(?P<id>ocd-jurisdiction/.+)/$', JurisdictionDetail.as_view()),
    url(r'^(?P<id>ocd-person/.+)/$', PersonDetail.as_view()),
    url(r'^(?P<id>ocd-event/.+)/$', EventDetail.as_view()),
    url(r'^(?P<id>ocd-vote/.+)/$', VoteDetail.as_view()),
    url(r'^(?P<id>ocd-organization/.+)/$', OrganizationDetail.as_view()),
)
