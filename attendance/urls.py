from django.contrib import admin
from django.urls import path, include
# from registration.views import update_attendance  # Import the update_attendance view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),  # Include the URLs from the registration app
    # path('update_attendance/<str:unique_identifier>/', update_attendance, name='update_attendance'),
]
