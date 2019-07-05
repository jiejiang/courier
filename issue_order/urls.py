# *- coding: utf-8 -*
from django.conf.urls import url, include
from . import views

urlpatterns = [
    url("^courier-batch/$", views.CourierBatchListView.as_view(), name="courier_batch"),
    url("^courier-batch/create/$", views.CourierBatchCreateView.as_view(), name="courier_batch_create"),
    url("^courier-batch/(?P<uuid>[\-a-z0-9]+)/download/$", views.CourierBatchDownloadView.as_view(),
        name="courier_batch_download"),
    url("^courier-batch/(?P<uuid>[\-a-z0-9]+)/delete/$",
        views.CourierBatchDeleteView.as_view(), name="courier_batch_delete"),
    url("^profile/(?P<username>.*)/$", views.ProfileView.as_view(), name="profile"),
]
