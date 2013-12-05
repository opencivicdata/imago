import csv
import urllib2
from optparse import make_option

from django.core.management.base import BaseCommand
from ...models import Division


class Command(BaseCommand):
    help = 'Loads in division ids from ocd-division file'

    option_list = BaseCommand.option_list + (
        make_option('--clear', action='store_true', dest='clear',
                    default=False, help='Clear divisions first.'),
    )

    def handle(self, *args, **options):
        if not args:
            print 'must specify arguments'
            return

        if options['clear']:
            Division.objects.all().delete()

        for arg in args:
            print arg, '...',
            count = 0
            for ocd_id, name in csv.reader(urllib2.urlopen(arg)):
                pieces = ocd_id.split('/')
                if pieces.pop(0) != 'ocd-division':
                    raise Exception('ID must start with ocd-division/')
                country = pieces.pop(0)
                if not country.startswith('country:'):
                    raise Exception('Second part of ID must be country:')
                else:
                    country = country.replace('country:', "")
                n = 1
                args = {}
                for piece in pieces:
                    type_, id_ = piece.split(':')
                    args['subtype%s' % n] = type_
                    args['subid%s' % n] = id_
                    n += 1

                Division.objects.create(id=ocd_id,
                                        display_name=name.decode('latin1'),
                                        country=country, **args)
                count += 1
            print count, 'objects'
