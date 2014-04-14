from __future__ import print_function
import re
import os
import csv
from datetime import datetime
from optparse import make_option
from subprocess import check_call

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...models import Division, DivisionGeometry, TemporalSet

OCDID_REPO = 'https://github.com/opencivicdata/ocd-division-ids.git'
LOCAL_REPO = '/tmp/ocdids'

def checkout_repo():
    if os.path.exists(LOCAL_REPO):
        cwd = os.getcwd()
        os.chdir(LOCAL_REPO)
        check_call(['git', 'pull'])
        os.chdir(cwd)
    else:
        check_call(['git', 'clone', OCDID_REPO, LOCAL_REPO])


def _ocd_id_to_args(ocd_id):
    pieces = ocd_id.split('/')
    if pieces.pop(0) != 'ocd-division':
        raise Exception('ID must start with ocd-division/')
    country = pieces.pop(0)
    if not country.startswith('country:'):
        raise Exception('Second part of ID must be country:')
    else:
        country = country.replace('country:', "")
    n = 1
    args = {'country': country}
    for piece in pieces:
        type_, id_ = piece.split(':')
        args['subtype%s' % n] = type_
        args['subid%s' % n] = id_
        n += 1
    return args

def load_divisions(clear=False):
    with transaction.atomic():
        if clear:
            print('deleting all divisions...')
            Division.objects.all().delete()

        # country csv
        count = 0
        filename = os.path.join(LOCAL_REPO, 'identifiers',
                                'country-{}.csv'.format(settings.IMAGO_COUNTRY))
        print('loading ' + filename)
        for row in csv.DictReader(open(filename)):
            args = _ocd_id_to_args(row['id'])
            args['redirect_id'] = row.get('sameAs', '')
            d = Division(id=row['id'], display_name=row['name'], **args)
            d.save()
            count += 1
        print(count, 'divisions')


def load_mapping(boundary_set_id, start, key, prefix, ignore, end=None, quiet=False):
    if ignore:
        ignore = re.compile(ignore)
    ignored = 0
    geoid_mapping = {}
    filename = os.path.join(LOCAL_REPO, 'identifiers',
                            'country-{}.csv'.format(settings.IMAGO_COUNTRY))
    for row in csv.DictReader(open(filename)):
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
        make_option('--clear', action='store_true', dest='clear',
                    default=False, help='Clear divisions first.'),
        make_option('--clear', action='store_true', dest='quiet',
                    default=False, help='Be somewhat quiet.'),
    )

    def handle(self, *args, **options):
        checkout_repo()
        load_divisions(options['clear'])
        for set_id, d in settings.IMAGO_BOUNDARY_MAPPINGS.items():
            load_mapping(set_id, quiet=options['quiet'], **d)
