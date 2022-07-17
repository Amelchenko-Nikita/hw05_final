from django.conf import settings
from django.core.paginator import Paginator


def page_paginator(queryset, request):
    limit = settings.POSTS_PER_PAGE
    paginator = Paginator(queryset, limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
