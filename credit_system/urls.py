from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from credits import views as credit_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', credit_views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('credits/', include('credits.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)