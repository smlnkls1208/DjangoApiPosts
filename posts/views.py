from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from .models import Post, Like
from .serializers import PostSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response

class MainPagePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20

class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MainPagePagination

    def get_queryset(self):
        return Post.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'

from .models import Comment
from .serializers import CommentSerializer

class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class PostCommentsListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id).order_by('created_at')

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)

    def get_serializer_context(self):
        return {'request': self.request}


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentOwnerOrReadOnly]
    lookup_field = 'id'

    def get_serializer_context(self):
        return {'request': self.request}


class LikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        like, created = Like.objects.get_or_create(post=post, user=user)

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return Response({
            "liked": liked,
            "likes_count": post.likes.count()
        }, status=status.HTTP_200_OK)