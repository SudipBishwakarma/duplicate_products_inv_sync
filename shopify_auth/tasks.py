import shopify
from .helpers import ShopifyHelper
from background_task import background
from app import helpers


@background()
def first_run(shop_url):
    store = ShopifyHelper(shop_url)
    store.activate_session()
    helpers.get_first_run(shop_url, False)
    store.bulk_remove()
    store.bulk_add_products()
    store.bulk_add_variants()
    store.create_webhook()
    store.clear_session()
    helpers.task_running(shop_url, False)
    print('Task: `First Run` completed successfully.')


# @background()
# def task_webhook_product_update(data):
#     shop_url = data.get('X-Shopify-Shop-Domain')
#     store = ShopifyHelper(shop_url)
#     store.activate_session()
#     store.webhook_product_update(data)
#     store.clear_session()
#     print('Task Webhook Product Update completed successfully.')

@background()
def inventory_levels_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_levels_update(data)
    store.clear_session()
    print('Task: `Inv. levels update` completed successfully.')


@background()
def inventory_items_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_items_update(data)
    store.clear_session()
    print('Task: `Inv. items update` completed successfully.')


@background()
def products_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.products_update(data)
    store.clear_session()
    print('Task: `Products update` completed successfully.')


@background()
def inventory_items_delete(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_items_delete(data)
    store.clear_session()
    print('Task: `Inv. items delete` completed successfully.')


@background()
def products_delete(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.products_delete(data)
    store.clear_session()
    print('Task: `Products delete` completed successfully.')
