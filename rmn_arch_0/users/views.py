from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View, TemplateView
from django.urls import reverse

import json
import random
from dal.autocomplete import Select2QuerySetView
from cities_light.models import City

from .forms import ProfileForm, EmailForm, SettingsForm
from .models import User


class UsernameCheckAJAXView(View):
    """
    Check whether the user name is available, if not suggest related names
    """
    SUGGESTION_NUM = 3

    def get(self, request):
        """
        Returns a JsonResponse with the following
            unique:         whether the username already exists
            suggestions:    if not unique, return SUGGESTION_NUM suggested names
        """
        username = request.GET.get('q', '')
        username = username.lower()
        if username == '':
            return HttpResponse(status=400)

        suggestions = []
        if not User.objects.filter(username=username).exists():
            unique = True
        else:
            unique = False
            while len(suggestions) < self.SUGGESTION_NUM:
                sug_name = username + str(random.random())[-4:]
                if not User.objects.filter(username=sug_name).exists():
                    suggestions.append(sug_name)

        return JsonResponse({
            'unique': unique,
            'suggestions': suggestions,
            })


class CityAutocompleteView(LoginRequiredMixin, Select2QuerySetView):
    """
    Used to server dal_select2 endpoint
    """
    def get_queryset(self):
        qs = City.objects.all()
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs


class ProfileEditView(LoginRequiredMixin, TemplateView):
    """
    Allow user to edit their profile
    """
    template_name = 'users/profile_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['form'] = ProfileForm(data=self.request.POST,
                files=self.request.FILES, instance=self.request.user.profile)
        else:
            context['form'] = ProfileForm(instance=self.request.user.profile)
        return context

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['form'].is_valid():
            context['form'].save()
            messages.success(request, 'You have successfully updated your profile')
            return HttpResponseRedirect(reverse('users:profile_edit'))
        return self.render_to_response(context)


class SettingsView(LoginRequiredMixin, TemplateView):
    """
    Allow user to chagne their settings
    """
    template_name = 'users/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['email_form'] = EmailForm(
                data=self.request.POST, instance=self.request.user)
            context['settings_form'] = SettingsForm(
                data=self.request.POST, instance=self.request.user.settings)
        else:
            context['email_form'] = EmailForm(instance=self.request.user)
            context['settings_form'] = SettingsForm(instance=self.request.user.settings)
        return context

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        email_form = context['email_form']
        settings_form = context['settings_form']
        if email_form.is_valid() and settings_form.is_valid():
            if email_form.has_changed():
                request.user.emailaddress_set.first().change(
                    request, email_form.cleaned_data['email'])
            if settings_form.has_changed():
                settings_form.save()
            messages.success(request, 'You have successfully updated your settings')
            return HttpResponseRedirect(reverse('users:settings'))
        return self.render_to_response(context)


class UserFollowAJAXView(LoginRequiredMixin, View):
    """
    Accepts AJAX request for logined user to follow other users
    Only accepts POST requests, requires
        user is logined
        username    string, name of the user
        follow      bool, whether to follow or unfollow the user
    returns HTTP 403 user not loggined
        HTTP 404 if not found
        HTTP 400 bad request
        HTTP 200 otherwise
    """
    raise_exception = True

    def post(self, request):
        payload = json.loads(request.body)
        username = payload.get('username', None)
        follow = payload.get('follow', None)
        if (username == None or follow == None):
            return HttpResponse(status=400)
        target_user = get_object_or_404(User, username=username)
        if target_user == request.user: # cant follow yourself
            return HttpResponse(status=400)
        if follow:
            request.user.relations.follows.add(target_user)
        else:
            request.user.relations.follows.remove(target_user)
        return HttpResponse(status=200)
