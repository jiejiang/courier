import sys
from django.core.management.base import BaseCommand
from django.utils import timezone

from order_api.models import Request
from order_api.tasks import submit_request

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('request_no', type=str)

    def handle(self, *args, **options):
        now = timezone.now()
        try:
            request = Request.objects.get(request_no=options['request_no'])
            submit_request(request, now, save=True)
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
