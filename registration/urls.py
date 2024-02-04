from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import participant_list, send_qr, send_qr_all, home, upload_csv, uploadPage, update_attendance, login

urlpatterns = [
    # path('', home, name='home'),  # URL pattern for the root path
    path('', login, name='login'),
    path('participants/', participant_list, name='participant_list'),
    path('send_qr/<int:participant_id>/<int:qr_type>/', send_qr, name='send_qr'),
    path('send_qr_all/<int:qr_type>/', send_qr_all, name='send_qr_all'),
    path('uploadFile/', uploadPage, name='uploadPage'),
    path('upload/', upload_csv, name='upload_csv'),
    path('update_attendance/<str:unique_identifier>/', update_attendance, name='update_attendance'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
