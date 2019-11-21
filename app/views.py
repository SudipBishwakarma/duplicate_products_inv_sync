from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import shopify
from shopify_auth.decorators import shopify_login_required
from shopify_auth.models import ShopifyStore, Product, Variant
from shopify_auth import tasks
from . import helpers


@shopify_login_required
def index(request):
    store_url = request.session['shopify']['shop_url']
    user = ShopifyStore.objects.get(myshopify_domain=store_url)
    if helpers.get_first_run(store_url):
        tasks.first_run(store_url, verbose_name=f'First run: {user.myshopify_domain}', creator=user)

    context = {'page_name': 'Home',
               'preferences': helpers.get_or_set_preferences(user)
               }
    return render(request, 'app/index.html', context)


def get_task_status(request):
    store_url = request.session['shopify']['shop_url']
    return JsonResponse(helpers.task_running(store_url))


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


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
