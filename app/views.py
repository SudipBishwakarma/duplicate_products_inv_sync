from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from shopify_auth.decorators import shopify_login_required
from shopify_auth.models import ShopifyStore
from shopify_auth import tasks
from . import helpers
from django.core.paginator import Paginator


@shopify_login_required
def index(request):
    store_url = request.session['shopify']['shop_url']
    store = ShopifyStore.objects.get(myshopify_domain=store_url)
    if helpers.get_first_run(store):
        tasks.first_run(store_url, verbose_name=f'First run: {store.myshopify_domain}', creator=store)

    context = {'page_name': 'Home',
               'preferences': helpers.get_or_set_preferences(store)}
    return render(request, 'app/index.html', context)


def get_task_status(request):
    store_url = request.session['shopify']['shop_url']
    store = ShopifyStore.objects.get(myshopify_domain=store_url)
    return JsonResponse(helpers.task_running(store))


def set_preferences(request):
    if request.method == 'POST':
        store_url = request.session['shopify']['shop_url']
        user = ShopifyStore.objects.get(myshopify_domain=store_url)
        activate = request.POST.get('activate')
        if activate:
            activate = True
        else:
            activate = False

        tags = request.POST.get('tags')
        helpers.get_or_set_preferences(user, activate, tags)

    return HttpResponse('Done')


def get_duplicates(request):
    store_url = request.session['shopify']['shop_url']
    store = ShopifyStore.objects.get(myshopify_domain=store_url)
    duplicates_list = helpers.get_duplicates(store)
    paginator = Paginator(duplicates_list, 25)

    page = request.GET.get('page')
    duplicates = paginator.get_page(page)
    no_image = 'https://cdn.shopify.com/s/assets/' \
               'no-image-2048-5e88c1b20e087fb7bbe9a3771824e743c244f437e4f8ba93bbf7b11b53f7824c_thumb.gif'
    return render(request, 'app/list.html',
                  {'store_url': store_url,
                   'page_name': 'Duplicates List',
                   'count': paginator.count,
                   'duplicates': duplicates,
                   'no_image': no_image})


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
