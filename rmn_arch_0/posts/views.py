from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Case, When, F, Q, IntegerField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, View
from django.urls import reverse

import json
import random

from .forms import PostForm, CommentForm, ReportForm
from .models import Post, PostImage, Rating, Comment, Report
from rmn_arch_0.users.models import User


class ElPaginatedListView(ListView):
    """
    Endlessly paginated list view
    Requires page_template_name to be set, which would be used for pages after the first
    """
    page_template_name = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_template_name'] = self.page_template_name
        return context

    def get(self, request, **kwargs):
        page_num = request.GET.get('page')
        if page_num == None or page_num == 1:
            return super().get(request, **kwargs)
        else:
            self.object_list = self.get_queryset()
            context = self.get_context_data(**kwargs)
            return render(request, self.page_template_name, context)


class HomeView(ElPaginatedListView):
    """
    Home page
    """
    template_name = 'posts/home.html'
    page_template_name = 'posts/home_posts.html'
    paginate_by = 20
    context_object_name = 'posts'

    def get_queryset(self):
        """
        Returns the posts objects order by newest (-id), annotate the current
        user/session user's ratings if applicable
        """
        q = Q(pk__in=[])    # Django ORM recognises this, always evaluates to False
        if self.request.user.is_authenticated:
            q = Q(rating__user=self.request.user)
        elif self.request.session.session_key:
            q = Q(rating__session_key=self.request.session.session_key)
        return Post.objects.annotate(
            rate = Case(
                When(q, then = F('rating__rate')),
                output_field = IntegerField()
            )
        ).filter(show = True
        ).order_by('-id', 'rate'
        ).distinct('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # randomly features some images
        last_featured = 0
        for i, post in enumerate(context['posts']):
            if (last_featured + 4 < i and random.random() < 0.5):
                last_featured = i
                post.extra_css_class = ' featured'

        # check whether the user is new
        if not (self.request.user.is_authenticated or self.request.session.session_key):
            self.request.session.create()
            context['first_visit'] = True
        return context


class RankView(TemplateView):
    """
    Page showing weekly/monthly ranings
    """
    template_name = 'posts/rank.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class FollowView(LoginRequiredMixin, ElPaginatedListView):
    """
    Page showing other users that the current user follows
    """
    template_name = 'posts/follow.html'
    page_template_name = 'posts/list_post.html'
    paginate_by = 10
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(
            user__in = self.request.user.relations.follows.all(),
            show = True,
            anonymous=False, #TODO test me
        ).order_by('-id')


class PostCreateModalView(LoginRequiredMixin, TemplateView):
    """
    Page allowing logined user to create new posts
    """
    template_name = 'posts/post_create.html'
    redirect_field_name  = 'ignored' # override default "next" so it redirect to home page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['form'] = PostForm(data=self.request.POST, files=self.request.FILES)
        else:
            context['form'] = PostForm()
        return context

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['form'].is_valid():
            post = context['form'].save(commit=False)
            post.user = request.user
            post.save()
            for file in request.FILES.getlist('images'):
                PostImage.objects.create(post=post, image=file)

            messages.success(request, 'You have created a new post')
            return HttpResponseRedirect(reverse('posts:home'))
        return self.render_to_response(context)


class PostDetailModalView(ElPaginatedListView):
    """
    Display indiviudal post as a modal content
    note this is subclass ListView (instead of DetailView) to facilitate pagniating comments
    """
    template_name = 'posts/post_detail_post.html'
    page_template_name = 'posts/post_detail_comments.html'
    paginate_by = 10
    context_object_name = 'comments'

    def get_object(self):
        """
        Return the actual Post object
        """
        return get_object_or_404(Post, uuid=self.kwargs['uuid'], show=True)

    def get_queryset(self):
        """
        Return the comments related to the given post
        """
        self.object = self.get_object()
        return Comment.objects.filter(post=self.object).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        # get current user/session user's rating
        rating = None
        if self.request.user.is_authenticated:
            rating = Rating.objects.filter(
                    user=self.request.user, post=self.object
                ).first()
        elif self.request.session.session_key:
            rating = Rating.objects.filter(
                    session_key=self.request.session.session_key, post=self.object
                ).first()
        context['rate'] = rating.rate if rating else None

        context['comment_form'] = CommentForm(prefix='comment')
        context['report_form'] = ReportForm(prefix='report')
        return context


class PostDetailView(PostDetailModalView):
    """
    Display individual post as a page
    """
    template_name = 'posts/post_detail.html'


class PostCommentAJAXView(LoginRequiredMixin, View):
    """
    Accepts AJAX request for new comment for logined user
    Returns comment_snippet of the new comment when successful, HTTP 400 otherwise
    """
    def post(self, request, **kwargs):
        post = Post.objects.get(uuid=self.kwargs['uuid'])
        comment_form = CommentForm(data=self.request.POST, prefix='comment')
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return render(request,
                'posts/snippets/comment_snippet.html',
                {'comment': comment, 'fade': True})
        return HttpResponse(status=400)


class PostReportAJAXView(LoginRequiredMixin, PostDetailModalView):
    """
    Accepts AJAX request for new reports for logined user
    Returns HTTP 200 when successful, HTTP 400 otherwise
    """
    def post(self, request, **kwargs):
        post = Post.objects.get(uuid=self.kwargs['uuid'])
        report, _ = Report.objects.get_or_create(user=request.user, post=post)
        report_form = ReportForm(data=self.request.POST, instance=report, prefix='report')
        if report_form.is_valid():
            report_form.save()
            return HttpResponse(status=200)
        return HttpResponse(status=400)


class PostRateAJAXView(View):
    """
    Endpoint allowing site visiter to rate a post
    Only accepts POST requests, requires
        uuid    string, uuid of the post
        rate    integer, desired rates
    returns HTTP 404 if not found
        HTTP 400 bad request
        HTTP 200 otherwise
    """
    def post(self, request):
        payload = json.loads(request.body)
        uuid = payload.get('uuid', None)
        rate = payload.get('rate', None)
        if (uuid == None or rate == None):
            return HttpResponse(status=400)
        post = get_object_or_404(Post, uuid=uuid)
        try:
            if request.user.is_authenticated:
                Rating.objects.update_or_create(
                    user=request.user,
                    post=post,
                    defaults={
                        'rate': rate,
                    })
            else:
                if not request.session.session_key:
                    request.session.create()
                Rating.objects.update_or_create(
                    session_key=request.session.session_key,
                    post=post,
                    defaults={
                        'rate': rate,
                    })
        except ValidationError:
            return HttpResponse(status=400)
        return HttpResponse(status=200)


class UserPostsView(ElPaginatedListView):
    """
    Display post made by a specific user
    """
    template_name = 'posts/user_posts.html'
    page_template_name = 'posts/list_post.html'
    paginate_by = 10
    context_object_name = 'posts'

    def get_queryset(self):
        user = User.objects.get(username=self.kwargs['username'])
        self.user = user
        return Post.objects.filter(user=user, anonymous=False, show=True).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curr_user'] = self.user
        return context
