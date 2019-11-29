from .models import FirstRun, Preferences
from shopify_auth.models import ShopifyStore, Product, Variant, Duplicate
from time import time

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
                'msg': f'Products count: {products}, Variants count: {variants}.',
                'table': render_duplicate_products(store)
            }
    except Exception as e:
        print(e)


def render_duplicate_products(store):
    """Generate table containing variants with duplicate sku."""
    data = """
        <div class="table-box">
            <table class="table table-bordered">
                <thead>
                    <tr>
                    <th scope="col">#</th>
                    <th scope="col">Product</th>
                    <th scope="col">Type</th>
                    <th scope="col">Vendor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <a href="#">
                                <img src="https://cdn.shopify.com/s/files/1/0046/3421/4518/products/3-Oysters-Ink-Bottle---Delicious---Aqua-Green-1_1c0624fe-aae0-4368-a21d-6ace978e2f9e_small.jpg?v=1562339374" alt="" width="50">
                            </a>
                        </td>
                        <td class="pro-anch">
                            <a href="#">
                                3 Oysters Ink Bottle - Delicious - Aqua Green
                            </a>
                            <p>SKU: 3O_06OYS006</p>
                        </td>
                        <td>
                            <p>Refill - Bottled Ink</p>
                        </td>
                        <td>
                            <p>3 Oysters</p>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <a href="#">
                                <img src="https://cdn.shopify.com/s/files/1/0046/3421/4518/products/3-Oysters-Ink-Bottle---Delicious---Aqua-Green-1_1c0624fe-aae0-4368-a21d-6ace978e2f9e_small.jpg?v=1562339374" alt="" width="50">
                            </a>
                        </td>
                        <td class="pro-anch">
                            <a href="#">
                                3 Oysters Ink Bottle - Delicious - Aqua Green
                            </a>
                            <p>SKU: 3O_06OYS006</p>
                        </td>
                        <td>
                            <p>Refill - Bottled Ink</p>
                        </td>
                        <td>
                            <p>3 Oysters</p>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    """
    return data


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
    duplicates = Duplicate.objects.raw(f"""
        SELECT v.variant_id as id, p.image, p.title as p_title, v.sku, p.product_id, p.type, p.vendor, v.title as
        v_title FROM shopify_auth_product AS p JOIN shopify_auth_variant AS v ON p.product_id=v.product_id WHERE
        p.store_id={_store} AND sku IN (SELECT sku FROM shopify_auth_variant WHERE store_id={_store} GROUP BY sku
        HAVING COUNT(sku) > 1)""")
    # dups = [items for items in duplicates]
    return duplicates


def _get_duplicates(store, start=0, end=25):
    duplicates = Duplicate.objects.get_duplicates(store, start, end)
    return duplicates
