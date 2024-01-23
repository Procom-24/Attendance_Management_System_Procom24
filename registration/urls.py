from django.urls import path
from .views import participant_list, send_qr, send_qr_all, home, update_attendance

urlpatterns = [
    path('', home, name='home'),  # URL pattern for the root path
    path('participants/', participant_list, name='participant_list'),
    path('send_qr/<int:participant_id>/<int:qr_type>/', send_qr, name='send_qr'),
    path('send_qr_all/<int:qr_type>/', send_qr_all, name='send_qr_all'),
    path('update_attendance/<str:unique_identifier>/', update_attendance, name='update_attendance'),
]
