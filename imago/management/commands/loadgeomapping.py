import csv
import urllib2
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from ...models import DivisionGeometry, TemporalSet


class Command(BaseCommand):
    args = '<boundary_set_id> <start_date (YYYY-MM-DD)> <mapping_url>'
    help = 'Creates temporal sets and division geometries.'

    option_list = BaseCommand.option_list + (
        make_option('--end', dest='end', default=None, help='optional end date'),
    )

    def handle(self, *args, **options):

        if len(args) != 3:
            raise CommandError('boundary_set_id, start_date, and mapping_url required')

        boundary_set_id, start, mapping_url = args
        end = options.get('end', None)

        start = datetime.strptime(start, '%Y-%m-%d')
        if end:
            end = datetime.strptime(end, '%Y-%m-%d')

        # build geo id mapping
        geoid_mapping = {}
        for ocd_id, geo_id in csv.reader(urllib2.urlopen(mapping_url)):
            geoid_mapping[geo_id] = ocd_id

        # delete temporal set & mappings if they exist
        tset = TemporalSet.objects.filter(boundary_set_id=boundary_set_id)
        if tset:
            print('Deleting existing TemporalSet')
            tset[0].geometries.all().delete()
            tset[0].delete()

        # create temporal set
        tset = TemporalSet.objects.create(boundary_set_id=boundary_set_id,
                                          start=start, end=end)
        for boundary in tset.boundary_set.boundaries.all():
            ocd_id = geoid_mapping.get(boundary.external_id)
            if ocd_id:
                DivisionGeometry.objects.create(division_id=ocd_id,
                                                temporal_set=tset,
                                                boundary=boundary)
            else:
                print 'unmatched external id', boundary, boundary.external_id
