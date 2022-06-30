"""rmn_arch_0 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.defaults import page_not_found
from django.urls import path, include


urlpatterns = [
    path('', include('rmn_arch_0.core.urls')),
    path('', include('rmn_arch_0.posts.urls')),
    path('messages/', include('rmn_arch_0.chat.urls')),
    path('users/', include('rmn_arch_0.users.urls')),
    # block the allauth email page explictly
    path('accounts/email/', page_not_found, {'exception': None}),
    path('accounts/', include('allauth.urls')),
    path('ctrl/', admin.site.urls),
    # should only work when debug = True according to doc
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
