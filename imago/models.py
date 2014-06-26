from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from boundaries.models import BoundarySet, Boundary
from pupa.models import Division


class TemporalSet(models.Model):
    boundary_set = models.OneToOneField(BoundarySet)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True)

    def __unicode__(self):
        return '{0} ({1}-{2})'.format(self.boundary_set, self.start, self.end or '')


class DivisionGeometry(models.Model):
    division = models.ForeignKey(Division, related_name='geometries')
    temporal_set = models.ForeignKey(TemporalSet, related_name='geometries')
    boundary = models.ForeignKey(Boundary, related_name='geometries')

    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.division, self.temporal_set, self.boundary)
