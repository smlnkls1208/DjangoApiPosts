from django.urls import path
from . import views

urlpatterns = [
    path('', views.PostListCreateView.as_view(), name='post-list-create'),
    path('<int:id>/', views.PostDetailView.as_view(), name='post-detail'),
]