from django.conf.urls import patterns
from imago.views import (MetadataList, MetadataDetail)

urlpatterns = patterns('',
    (r'^metadata/$', MetadataList.as_view()),
    (r'^metadata/(?P<id>.+)/$', MetadataDetail.as_view()),
)
