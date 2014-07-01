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
    url(r'^(?P<pk>ocd-jurisdiction/.+)/$', JurisdictionDetail.as_view()),
    url(r'^(?P<pk>ocd-person/.+)/$', PersonDetail.as_view()),
    url(r'^(?P<pk>ocd-event/.+)/$', EventDetail.as_view()),
    url(r'^(?P<pk>ocd-vote/.+)/$', VoteDetail.as_view()),
    url(r'^(?P<pk>ocd-organization/.+)/$', OrganizationDetail.as_view()),
)
