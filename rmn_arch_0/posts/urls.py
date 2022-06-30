from django.urls import path
from .views import (
    HomeView,
    RankView,
    FollowView,
    PostCreateModalView,
    PostDetailModalView,
    PostDetailView,
    PostCommentAJAXView,
    PostReportAJAXView,
    PostRateAJAXView,
    UserPostsView,
)

app_name = 'posts'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('rank/', RankView.as_view(), name='rank'),
    path('follow/', FollowView.as_view(), name='follow'),
    path('posts/create/m/', PostCreateModalView.as_view(), name='post_create_modal'),
    path('posts/<uuid:uuid>/m/', PostDetailModalView.as_view(), name='post_detail_modal'),
    path('posts/<uuid:uuid>/', PostDetailView.as_view(), name='post_detail'),
    path('posts/<uuid:uuid>/comment/', PostCommentAJAXView.as_view(), name='post_comment'),
    path('posts/<uuid:uuid>/report/', PostReportAJAXView.as_view(), name='post_report'),
    path('posts/rate/', PostRateAJAXView.as_view(), name='rate'),
    path('users/<str:username>/posts/', UserPostsView.as_view(), name='user_posts'),
]
