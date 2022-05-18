from django.conf import settings
from django.core.paginator import Paginator


def paginator(posts_list, request):
    """Пагинация страниц"""
    pag = Paginator(posts_list, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = pag.get_page(page_number)
    return page_obj
