from django.urls import path
from .views import (
    UsernameCheckAJAXView,
    CityAutocompleteView,
    ProfileEditView,
    SettingsView,
    UserFollowAJAXView,
)

app_name = 'users'

urlpatterns = [
    path('username-check/', UsernameCheckAJAXView.as_view(), name='username_check'),
    path('dal-city/', CityAutocompleteView.as_view(), name='city_autocomplete'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('follow/', UserFollowAJAXView.as_view(), name='follow'),
]
