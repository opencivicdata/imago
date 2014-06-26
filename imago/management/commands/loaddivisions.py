from __future__ import print_function
import re
import os
import csv
from datetime import datetime
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...models import Division, DivisionGeometry, TemporalSet



def load_mapping(boundary_set_id, start, key, prefix, ignore, end=None, quiet=False):
    if ignore:
        ignore = re.compile(ignore)
    ignored = 0
    geoid_mapping = {}
    filename = os.path.join(LOCAL_REPO, 'identifiers',
                            'country-{}.csv'.format(settings.IMAGO_COUNTRY))
    for row in csv.DictReader(open(filename, encoding='utf8')):
        if row[key]:
            geoid_mapping[row[key]] = row['id']

    print('processing', boundary_set_id)

    # delete temporal set & mappings if they exist
    tset = TemporalSet.objects.filter(boundary_set_id=boundary_set_id)
    if tset:
        print('Deleting existing TemporalSet')
        tset[0].geometries.all().delete()
        tset[0].delete()

    # create temporal set
    tset = TemporalSet.objects.create(boundary_set_id=boundary_set_id, start=start, end=end)
    for boundary in tset.boundary_set.boundaries.all():
        ocd_id = geoid_mapping.get(prefix+boundary.external_id)
        if ocd_id:
            DivisionGeometry.objects.create(division_id=ocd_id, temporal_set=tset,
                                            boundary=boundary)
        elif not ignore or not ignore.match(boundary.name):
            if not quiet:
                print('unmatched external id', boundary, boundary.external_id)
        else:
            ignored += 1

    if ignored:
        print('ignored {} unmatched external ids'.format(ignored))


class Command(BaseCommand):
    help = 'Loads in division ids'

    option_list = BaseCommand.option_list + (
        make_option('--quiet', action='store_true', dest='quiet',
                    default=False, help='Be somewhat quiet.'),
    )

    def handle(self, *args, **options):
        for set_id, d in settings.IMAGO_BOUNDARY_MAPPINGS.items():
            load_mapping(set_id, quiet=options['quiet'], **d)
