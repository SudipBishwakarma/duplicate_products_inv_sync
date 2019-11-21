from .models import FirstRun, Preferences
from shopify_auth.models import ShopifyStore, Product, Variant


def get_first_run(store_url, status=None):
    """Checks if the app is run for the first time."""
    obj, created = FirstRun.objects.get_or_create(myshopify_domain=store_url)
    if type(status) is bool and not status:
        obj.status = status
        obj.save()
    return obj.status


def task_running(store_url, task=None):
    """Check whether background task is running or completed for first run."""
    try:
        obj = FirstRun.objects.get(myshopify_domain=store_url)
        if type(task) is bool:
            obj.bg_task = task
            obj.save()

        if obj.bg_task:
            return {'bg_task': obj.bg_task, 'msg': 'Catalog sync is currently running as background task.'}
        else:
            user = ShopifyStore.objects.get(myshopify_domain=store_url)
            products = Product.objects.filter(store=user).count()
            variants = Variant.objects.filter(store=user).count()
            return {
                'bg_task': obj.bg_task,
                'msg': f'Products count: {products}, Variants count: {variants}.'
            }
    except Exception as e:
        print(e)


def get_or_set_preferences(store, activate=None, tags=None):
    obj, created = Preferences.objects.get_or_create(store=store)
    if type(activate) is bool:
        obj.activate = activate
        obj.save()
    if type(tags) is str:
        obj.tags = tags
        obj.save()
    return obj
