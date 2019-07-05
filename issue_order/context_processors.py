from models import Route

def routes(request):
    return {
        'routes': Route.objects.order_by('name')
    }