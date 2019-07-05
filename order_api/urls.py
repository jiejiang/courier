# *- coding: utf-8 -*
from django.conf.urls import url, include
from order_api import views
from rest_framework.routers import DefaultRouter, APIRootView
from rest_framework.documentation import include_docs_urls

class APIRootView(APIRootView):
    """
    CNExpress API所支持的API方法列举如下：
    """
    pass

router = DefaultRouter()
router.APIRootView = APIRootView
router.register(r'account', views.AccountViewSet, base_name='account')
router.register(r'products', views.ProductViewSet, base_name='product')
router.register(r'cities', views.CityViewSet, base_name='city')
router.register(r'requests', views.RequestViewSet, base_name='request')
router.register(r'packages', views.PackageViewSet, base_name='package')
router.register(r'waybills', views.WaybillViewSet, base_name='waybill')
router.register(r'waybills/request', views.RequestWaybillViewSet, base_name='request-waybill')
router.register(r'tracking', views.TrackingViewSet, base_name='tracking')


slashless_router = DefaultRouter(trailing_slash=False)
slashless_router.registry = router.registry[:]

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(slashless_router.urls)),
    url(r'^api/auth/', include('rest_framework.urls')),
    url(r'^api/docs/', include_docs_urls(title='CNExpress API')),
]

