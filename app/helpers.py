from .models import FirstRun, Preferences
from shopify_auth.models import ShopifyStore, Product, Variant, Duplicate


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
            duplicates = get_duplicates(store)
            data = f'Variants with duplicate sku: {len(duplicates)}'
            return {
                'bg_task': obj.bg_task,
                'msg': f'Products count: {products}, Variants count: {variants}.',
                'table': data
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


def get_duplicates(store):
    _store = store.id
    product_table = Product.objects.model._meta.db_table
    variant_table = Variant.objects.model._meta.db_table
    duplicates = Duplicate.objects.raw(f"""
        SELECT v.variant_id as id, p.image, p.title as p_title, v.sku, p.product_id, p.type, p.vendor, v.title as
        v_title FROM {product_table} AS p JOIN {variant_table} AS v ON p.product_id=v.product_id WHERE
        p.store_id={_store} AND sku IN (SELECT sku FROM {variant_table} WHERE store_id={_store} GROUP BY sku
        HAVING COUNT(sku) > 1)""")
    return duplicates


def _get_duplicates(store, start=0, end=25):
    duplicates = Duplicate.objects.get_duplicates(store, start, end)
    return duplicates
