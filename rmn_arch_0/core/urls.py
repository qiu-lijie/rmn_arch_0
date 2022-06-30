from django.urls import path
from .views import terms_and_conditions

app_name = 'core'

urlpatterns = [
    path('terms-and-conditions/', terms_and_conditions, name='terms_and_conditions'),
]
