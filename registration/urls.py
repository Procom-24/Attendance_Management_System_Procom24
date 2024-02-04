from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import participant_list, send_qr, send_qr_all, home, upload_csv, uploadPage,scan_qr,mark_attendance

urlpatterns = [
    path('', home, name='home'),  # URL pattern for the root path
    path('participants/', participant_list, name='participant_list'),
    path('send_qr/<int:participant_id>/<int:qr_type>/', send_qr, name='send_qr'),
    path('send_qr_all/<int:qr_type>/', send_qr_all, name='send_qr_all'),
    path('uploadFile/', uploadPage, name='uploadPage'),
    path('upload/', upload_csv, name='upload_csv'),
    path('scan-qr/', scan_qr, name='scan_qr'),
    path('mark-attendance/', mark_attendance, name='mark_attendance'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
