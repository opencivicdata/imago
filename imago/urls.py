from django.conf.urls import patterns
from imago.views import (MetadataList,
                         OrganizationList,
                         PeopleList,
                         BillList,
                         MetadataDetail,
                         OrganizationDetail,
                         PersonDetail,
                         BillDetail,
                        )

urlpatterns = patterns('',
    (r'^metadata/$', MetadataList.as_view()),
    (r'^organizations/$', OrganizationList.as_view()),
    (r'^people/$', PeopleList.as_view()),
    (r'^bills/$', BillList.as_view()),

    # detail views
    (r'^(?P<id>ocd-jurisdiction/.+)/$', MetadataDetail.as_view()),
    (r'^(?P<id>ocd-organization/[0-9a-f-]+)/$', OrganizationDetail.as_view()),
    (r'^(?P<id>ocd-person/[0-9a-f-]+)/$', PersonDetail.as_view()),
    (r'^(?P<id>ocd-bill/[0-9a-f-]+)/$', BillDetail.as_view()),
)
