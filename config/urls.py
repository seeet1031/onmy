from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from appointments.views import google_callback
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.views.i18n import set_language

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('callback/', google_callback, name='google_callback'),  # ここでcallbackを追加
    path('set_language/', set_language, name='set_language'),

]
urlpatterns += i18n_patterns(
    # 多言語対応が必要なパスをここに追加
    path('accounts/', include('accounts.urls')),
)
