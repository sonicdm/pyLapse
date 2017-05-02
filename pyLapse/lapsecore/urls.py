from django.conf.urls import url, include
from rest_framework import routers
import api
import views

router = routers.DefaultRouter()
router.register(r'camera', api.CameraViewSet)
router.register(r'capture', api.CaptureViewSet)
router.register(r'capturecamera', api.CaptureCameraViewSet)
router.register(r'captureschedule', api.CaptureScheduleViewSet)
router.register(r'collection', api.CollectionViewSet)
router.register(r'collectionexport', api.CollectionExportViewSet)
router.register(r'exportpreset', api.ExportPresetViewSet)
router.register(r'scheduler', api.SchedulerViewSet)
router.register(r'exporttimefilter', api.ExportTimeFilterViewSet)
router.register(r'collectionfile', api.CollectionFileViewSet)
router.register(r'scheduledays', api.ScheduleDaysViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    url(r'^api/v1/', include(router.urls)),
    url(r'^$', views.CaptureListView)
)

urlpatterns += (
    # urls for Camera
    url(r'^lapsecore/camera/$', views.CameraListView.as_view(), name='lapsecore_camera_list'),
    url(r'^lapsecore/camera/create/$', views.CameraCreateView.as_view(), name='lapsecore_camera_create'),
    url(r'^lapsecore/camera/detail/(?P<pk>\S+)/$', views.CameraDetailView.as_view(), name='lapsecore_camera_detail'),
    url(r'^lapsecore/camera/update/(?P<pk>\S+)/$', views.CameraUpdateView.as_view(), name='lapsecore_camera_update'),
)

urlpatterns += (
    # urls for Capture
    url(r'^lapsecore/capture/$', views.CaptureListView.as_view(), name='lapsecore_capture_list'),
    url(r'^lapsecore/capture/create/$', views.CaptureCreateView.as_view(), name='lapsecore_capture_create'),
    url(r'^lapsecore/capture/detail/(?P<slug>\S+)/$', views.CaptureDetailView.as_view(), name='lapsecore_capture_detail'),
    url(r'^lapsecore/capture/update/(?P<slug>\S+)/$', views.CaptureUpdateView.as_view(), name='lapsecore_capture_update'),
)

urlpatterns += (
    # urls for CaptureCamera
    url(r'^lapsecore/capturecamera/$', views.CaptureCameraListView.as_view(), name='lapsecore_capturecamera_list'),
    url(r'^lapsecore/capturecamera/create/$', views.CaptureCameraCreateView.as_view(), name='lapsecore_capturecamera_create'),
    url(r'^lapsecore/capturecamera/detail/(?P<pk>\S+)/$', views.CaptureCameraDetailView.as_view(), name='lapsecore_capturecamera_detail'),
    url(r'^lapsecore/capturecamera/update/(?P<pk>\S+)/$', views.CaptureCameraUpdateView.as_view(), name='lapsecore_capturecamera_update'),
)

urlpatterns += (
    # urls for CaptureSchedule
    url(r'^lapsecore/captureschedule/$', views.CaptureScheduleListView.as_view(), name='lapsecore_captureschedule_list'),
    url(r'^lapsecore/captureschedule/create/$', views.CaptureScheduleCreateView.as_view(), name='lapsecore_captureschedule_create'),
    url(r'^lapsecore/captureschedule/detail/(?P<pk>\S+)/$', views.CaptureScheduleDetailView.as_view(), name='lapsecore_captureschedule_detail'),
    url(r'^lapsecore/captureschedule/update/(?P<pk>\S+)/$', views.CaptureScheduleUpdateView.as_view(), name='lapsecore_captureschedule_update'),
)

urlpatterns += (
    # urls for Collection
    url(r'^lapsecore/collection/$', views.CollectionListView.as_view(), name='lapsecore_collection_list'),
    url(r'^lapsecore/collection/create/$', views.CollectionCreateView.as_view(), name='lapsecore_collection_create'),
    url(r'^lapsecore/collection/detail/(?P<slug>\S+)/$', views.CollectionDetailView.as_view(), name='lapsecore_collection_detail'),
    url(r'^lapsecore/collection/update/(?P<slug>\S+)/$', views.CollectionUpdateView.as_view(), name='lapsecore_collection_update'),
)

urlpatterns += (
    # urls for CollectionExport
    url(r'^lapsecore/collectionexport/$', views.CollectionExportListView.as_view(), name='lapsecore_collectionexport_list'),
    url(r'^lapsecore/collectionexport/create/$', views.CollectionExportCreateView.as_view(), name='lapsecore_collectionexport_create'),
    url(r'^lapsecore/collectionexport/detail/(?P<slug>\S+)/$', views.CollectionExportDetailView.as_view(), name='lapsecore_collectionexport_detail'),
    url(r'^lapsecore/collectionexport/update/(?P<slug>\S+)/$', views.CollectionExportUpdateView.as_view(), name='lapsecore_collectionexport_update'),
)

urlpatterns += (
    # urls for ExportPreset
    url(r'^lapsecore/exportpreset/$', views.ExportPresetListView.as_view(), name='lapsecore_exportpreset_list'),
    url(r'^lapsecore/exportpreset/create/$', views.ExportPresetCreateView.as_view(), name='lapsecore_exportpreset_create'),
    url(r'^lapsecore/exportpreset/detail/(?P<slug>\S+)/$', views.ExportPresetDetailView.as_view(), name='lapsecore_exportpreset_detail'),
    url(r'^lapsecore/exportpreset/update/(?P<slug>\S+)/$', views.ExportPresetUpdateView.as_view(), name='lapsecore_exportpreset_update'),
)

urlpatterns += (
    # urls for Scheduler
    url(r'^lapsecore/scheduler/$', views.SchedulerListView.as_view(), name='lapsecore_scheduler_list'),
    url(r'^lapsecore/scheduler/create/$', views.SchedulerCreateView.as_view(), name='lapsecore_scheduler_create'),
    url(r'^lapsecore/scheduler/detail/(?P<slug>\S+)/$', views.SchedulerDetailView.as_view(), name='lapsecore_scheduler_detail'),
    url(r'^lapsecore/scheduler/update/(?P<slug>\S+)/$', views.SchedulerUpdateView.as_view(), name='lapsecore_scheduler_update'),
)

urlpatterns += (
    # urls for ExportTimeFilter
    url(r'^lapsecore/exporttimefilter/$', views.ExportTimeFilterListView.as_view(), name='lapsecore_exporttimefilter_list'),
    url(r'^lapsecore/exporttimefilter/create/$', views.ExportTimeFilterCreateView.as_view(), name='lapsecore_exporttimefilter_create'),
    url(r'^lapsecore/exporttimefilter/detail/(?P<slug>\S+)/$', views.ExportTimeFilterDetailView.as_view(), name='lapsecore_exporttimefilter_detail'),
    url(r'^lapsecore/exporttimefilter/update/(?P<slug>\S+)/$', views.ExportTimeFilterUpdateView.as_view(), name='lapsecore_exporttimefilter_update'),
)

urlpatterns += (
    # urls for CollectionFile
    url(r'^lapsecore/collectionfile/$', views.CollectionFileListView.as_view(), name='lapsecore_collectionfile_list'),
    url(r'^lapsecore/collectionfile/create/$', views.CollectionFileCreateView.as_view(), name='lapsecore_collectionfile_create'),
    url(r'^lapsecore/collectionfile/detail/(?P<slug>\S+)/$', views.CollectionFileDetailView.as_view(), name='lapsecore_collectionfile_detail'),
    url(r'^lapsecore/collectionfile/update/(?P<slug>\S+)/$', views.CollectionFileUpdateView.as_view(), name='lapsecore_collectionfile_update'),
)

urlpatterns += (
    # urls for ScheduleDays
    url(r'^lapsecore/scheduledays/$', views.ScheduleDaysListView.as_view(), name='lapsecore_scheduledays_list'),
    url(r'^lapsecore/scheduledays/create/$', views.ScheduleDaysCreateView.as_view(), name='lapsecore_scheduledays_create'),
    url(r'^lapsecore/scheduledays/detail/(?P<slug>\S+)/$', views.ScheduleDaysDetailView.as_view(), name='lapsecore_scheduledays_detail'),
    url(r'^lapsecore/scheduledays/update/(?P<slug>\S+)/$', views.ScheduleDaysUpdateView.as_view(), name='lapsecore_scheduledays_update'),
)

