from django.shortcuts import render


def terms_and_conditions(request):
    return render(request, 'core/terms_and_conditions.html')
