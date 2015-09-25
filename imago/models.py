from django.contrib.gis.db import models
from boundaries.models import Boundary
from opencivicdata.models import Division


class DivisionGeometry(models.Model):
    division = models.ForeignKey(Division, related_name='geometries')
    boundary = models.ForeignKey(Boundary, related_name='geometries')

    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.division, self.boundary)
