from django.conf.urls import patterns, url
from imago.views import (JurisdictionList,
                         JurisdictionDetail,)

urlpatterns = patterns(
    '',
    url(r'^jurisdictions/$', JurisdictionList.as_view()),

    # detail views
    url(r'^(?P<id>ocd-jurisdiction/.+)/$', JurisdictionDetail.as_view()),
)
