
# recorder/urls.py
from django.urls import path
from . import views

app_name = 'recorder'

urlpatterns = [
    path('', views.home, name='home'),
    path('record/<str:username>/', views.record, name='record'),
    path('save_recording/', views.save_recording, name='save_recording'),
    path('download/<str:username>/', views.download_user_recordings, name='download_recordings'),
    path('clear/<str:username>/', views.clear_recordings, name='clear_recordings'),

]
