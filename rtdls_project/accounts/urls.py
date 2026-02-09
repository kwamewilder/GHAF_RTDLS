from django.urls import path

from .views import SecureLoginView, logout_view, profile_view

urlpatterns = [
    path('login/', SecureLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
