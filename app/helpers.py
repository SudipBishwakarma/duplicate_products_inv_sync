from .models import FirstRun, Preferences
from shopify_auth.models import ShopifyStore, Product, Variant


def get_first_run(store, status=None):
    """Checks if the app is run for the first time."""
    obj, created = FirstRun.objects.get_or_create(store=store)
    if type(status) is bool and not status:
        obj.status = status
        obj.save()
    return obj.status


def task_running(store, task=None):
    """Check whether background task is running or completed for first run."""
    try:
        obj = FirstRun.objects.get(store=store)
        if type(task) is bool:
            obj.bg_task = task
            obj.save()

        if obj.bg_task:
            return {'bg_task': obj.bg_task, 'msg': 'Catalog sync is currently running as background task.'}
        else:
            products = Product.objects.filter(store=store).count()
            variants = Variant.objects.filter(store=store).count()
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
