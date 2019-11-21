from django.urls import path
from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('bg_task/', views.get_task_status, name='bg_task'),
    path('preferences/', views.set_preferences, name='preferences'),
]

# handler404 = views.handler404
# handler500 = views.handler500
