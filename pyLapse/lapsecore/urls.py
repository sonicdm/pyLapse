from django.conf.urls import url, include
from rest_framework import routers
import api
import views

router = routers.DefaultRouter()
router.register(r'camera', api.CameraViewSet)
router.register(r'capture', api.CaptureViewSet)
router.register(r'captureschedule', api.CaptureScheduleViewSet)
router.register(r'capturecamera', api.CaptureCameraViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    url(r'^api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Camera
    url(r'^lapsecore/camera/$', views.CameraListView.as_view(), name='lapsecore_camera_list'),
    url(r'^lapsecore/camera/create/$', views.CameraCreateView.as_view(), name='lapsecore_camera_create'),
    url(r'^lapsecore/camera/detail/(?P<slug>\S+)/$', views.CameraDetailView.as_view(), name='lapsecore_camera_detail'),
    url(r'^lapsecore/camera/update/(?P<slug>\S+)/$', views.CameraUpdateView.as_view(), name='lapsecore_camera_update'),
)

urlpatterns += (
    # urls for Capture
    url(r'^lapsecore/capture/$', views.CaptureListView.as_view(), name='lapsecore_capture_list'),
    url(r'^lapsecore/capture/create/$', views.CaptureCreateView.as_view(), name='lapsecore_capture_create'),
    url(r'^lapsecore/capture/detail/(?P<slug>\S+)/$', views.CaptureDetailView.as_view(), name='lapsecore_capture_detail'),
    url(r'^lapsecore/capture/update/(?P<slug>\S+)/$', views.CaptureUpdateView.as_view(), name='lapsecore_capture_update'),
)

urlpatterns += (
    # urls for CaptureSchedule
    url(r'^lapsecore/captureschedule/$', views.CaptureScheduleListView.as_view(), name='lapsecore_captureschedule_list'),
    url(r'^lapsecore/captureschedule/create/$', views.CaptureScheduleCreateView.as_view(), name='lapsecore_captureschedule_create'),
    url(r'^lapsecore/captureschedule/detail/(?P<slug>\S+)/$', views.CaptureScheduleDetailView.as_view(),
        name='lapsecore_captureschedule_detail'),
    url(r'^lapsecore/captureschedule/update/(?P<slug>\S+)/$', views.CaptureScheduleUpdateView.as_view(),
        name='lapsecore_captureschedule_update'),
)

urlpatterns += (
    # urls for CaptureCamera
    url(r'^lapsecore/capturecamera/$', views.CaptureCameraListView.as_view(), name='lapsecore_capturecamera_list'),
    url(r'^lapsecore/capturecamera/create/$', views.CaptureCameraCreateView.as_view(),
        name='lapsecore_capturecamera_create'),
    url(r'^lapsecore/capturecamera/detail/(?P<slug>\S+)/$', views.CaptureCameraDetailView.as_view(),
        name='lapsecore_capturecamera_detail'),
    url(r'^lapsecore/capturecamera/update/(?P<slug>\S+)/$', views.CaptureCameraUpdateView.as_view(),
        name='lapsecore_capturecamera_update'),
)

