import sys, json
from django.core.management.base import BaseCommand

from track_order.kuaidi100 import query

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('route', type=str)
        parser.add_argument('number', type=str)

    def handle(self, *args, **options):
        try:
            print json.dumps(query(options['route'], options['number']), sort_keys=True, indent=4,
                             separators=(',', ': '), ensure_ascii=False)
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
