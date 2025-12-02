from django.urls import path
from . import views

urlpatterns = [
    path('', views.PostListCreateView.as_view(), name='post-list-create'),
    path('<int:id>/', views.PostDetailView.as_view(), name='post-detail'),
    path('<int:post_id>/comments/', views.PostCommentsListView.as_view(), name='post-comments'),
    path('<int:post_id>/comments/<int:id>/', views.CommentDetailView.as_view(), name='comment-detail'),
    path('<int:post_id>/like/', views.LikeToggleView.as_view(), name='post-like'),
]


