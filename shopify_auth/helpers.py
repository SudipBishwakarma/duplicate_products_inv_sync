from django.conf import settings
from django.shortcuts import reverse
import hmac
import hashlib
import base64
import shopify
import json
from time import time
import math

from .models import ShopifyStore, Product, Variant
from app.helpers import get_or_set_preferences

SECRET = settings.SHOPIFY_API_SECRET
URL = settings.URL


def verify_webhook(data, hmac_header):
    digest = hmac.new(SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))


def match_tags(tags, _tags):
    tags_list = tags.split(', ')
    _tags_list = _tags.split(',')
    found = False
    for _ in _tags_list:
        for tag in tags_list:
            if _ == tag:
                found = True
                break
        if found:
            return found
    return found


class ShopifyHelper:
    def __init__(self, myshopify_domain):
        self._myshopify_domain = myshopify_domain
        try:
            self._user = ShopifyStore.objects.get(myshopify_domain=self._myshopify_domain)
            self._preferences = get_or_set_preferences(self._user)
        except Exception as e:
            raise e

        self._token, self._url = self._user.access_token, self._user.myshopify_domain

    def activate_session(self):
        shopify_session = shopify.Session(self._url, settings.SHOPIFY_API_VERSION, self._token)
        shopify.ShopifyResource.activate_session(shopify_session)

    def clear_session(self):
        shopify.ShopifyResource.clear_session()

    def get_user(self):
        return self._user

    def create_webhook(self):
        """Create webhook for listening events for inventory adjustment, product and variant deletion."""
        def address(name): return f"https://{URL + reverse('shopify_auth:' + name)}"
        try:
            webhooks = shopify.Webhook.find()
            if webhooks:
                for _ in webhooks:
                    _.destroy()
            webhook = shopify.Webhook()
            webhook.create({'topic': 'inventory_levels/update', 'address': address('inventory_levels_update')})
            webhook.create({'topic': 'inventory_items/update', 'address': address('inventory_items_update')})
            webhook.create({'topic': 'products/update', 'address': address('products_update')})
            webhook.create({'topic': 'inventory_items/delete', 'address': address('inventory_items_delete')})
            webhook.create({'topic': 'products/delete', 'address': address('products_delete')})
        except Exception as e:
            print(e)

    def inventory_levels_update(self, data):
        inventory_item_id = data.get('inventory_item_id')
        available = data.get('available')
        try:
            if self._preferences.activate:
                variant, created = Variant.objects.get_or_create(store=self._user, inventory_item_id=inventory_item_id)
                if created:
                    client = shopify.GraphQL()
                    query = '''
                        query {
                            inventoryItem(id: "gid://shopify/InventoryItem/%s") {
                                variant {
                                    id
                                    title
                                    price
                                    sku
                                    inventoryQuantity
                                    product {
                                        id
                                        title
                                        vendor
                                        productType
                                        tags
                                        featuredImage {
                                            transformedSrc(maxWidth: 50)
                                        }
                                    }
                                }
                            }
                        }
                    ''' % inventory_item_id
                    result = json.loads(client.execute(query))['data']['inventoryItem']
                    if result:
                        variant.variant_id = int(result['variant']['id'].split('/')[-1])
                        variant.product_id = int(result['variant']['product']['id'].split('/')[-1])
                        variant.title = result['variant']['title']
                        variant.price = float(result['variant']['price'])
                        variant.sku = result['variant']['sku'].strip()
                        variant.qty = result['variant']['inventoryQuantity']
                        variant.save()

                        product, _created = Product.objects.get_or_create(store=self._user, product_id=variant.product_id)
                        if _created:
                            product.title = result['variant']['product']['title']
                            product.vendor = result['variant']['product']['vendor']
                            product.tags = ', '.join(tag for tag in result['variant']['product']['tags'])
                            product.type = result['variant']['product']['productType']
                            product.image = result['variant']['product']['featuredImage']['transformedSrc']
                            product.save()

                if variant.qty != available or created:
                    variant.qty = available
                    variant.save()
                    print('Inventory synced with local db for variant %s' % variant.id)
                    if variant.sku != '':
                        variants = Variant.objects.filter(store=self._user, sku=variant.sku)
                        _tags = self._preferences.tags
                        if _tags != '':
                            for _ in variants:
                                _product = Product.objects.get(store=self._user, product_id=_.product_id)
                                tags = _product.tags
                                found = match_tags(tags, _tags)
                                if found:
                                    break
                        else:
                            found = True

                        if found:
                            for _ in variants:
                                if _.id != variant.id:
                                    inv_item = shopify.InventoryLevel.find_first(inventory_item_ids=_.inventory_item_id)
                                    shopify.InventoryLevel.set(
                                        inventory_item_id=_.inventory_item_id,
                                        location_id=inv_item.location_id,
                                        available=available)
                                    _.qty = available
                                    _.save()
                                    print(f'Inventory synced with variant {_.id}')
        except Exception as e:
            print(e)

    def inventory_items_update(self, data):
        inventory_item_id = data.get('id')
        sku = data.get('sku').strip()
        try:
            if self._preferences.activate:
                variant = Variant.objects.get(store=self._user, inventory_item_id=inventory_item_id)
                variant.sku = sku
                variants = Variant.objects.filter(store=self._user, sku=sku)
                for _ in variants:
                    if _.id != variant.id:
                        variant.qty = _.qty
                        break
                variant.save()
                inv_item = shopify.InventoryLevel.find_first(inventory_item_ids=inventory_item_id)
                shopify.InventoryLevel.set(
                    inventory_item_id=inventory_item_id,
                    location_id=inv_item.location_id,
                    available=variant.qty)
                print('Inventory and sku synced for variant %s' % variant.id)
        except Exception as e:
            print(e)

    def products_update(self, data):
        product_id = data.get('id')
        title= data.get('title')
        vendor = data.get('vendor')
        tags = data.get('tags')
        p_type = data.get('product_type')
        try:
            if self._preferences.activate:
                product = Product.objects.get(store=self._user, product_id=product_id)
                product.title = title
                product.vendor = vendor
                product.tags = tags
                product.type = p_type
                product.save()
                print("Product: %s" % product.id)
        except Exception as e:
            print(e)

    def inventory_items_delete(self, data):
        inventory_item_id = data.get('id')
        try:
            if self._preferences.activate:
                variant = Variant.objects.get(store=self._user, inventory_item_id=inventory_item_id)
                variant.delete()
        except Exception as e:
            print(e)

    def products_delete(self, data):
        product_id = data.get('id')
        try:
            variants = Variant.objects.filter(store=self._user, product_id=product_id)
            variants.delete()
            product = Product.objects.get(store=self._user, product_id=product_id)
            product.delete()
        except Exception as e:
            print(e)

    def bulk_remove(self):
        Product.objects.filter(store=self._user).delete()
        Variant.objects.filter(store=self._user).delete()

    def bulk_add_products(self, limit=250):
        def get_products(page_info='', chunk=1, limit=''):
            """Fetch products recursively."""
            cache = page_info
            products = shopify.Product.find(limit=limit, page_info=page_info)
            product_models = [Product(store=self._user,
                                      product_id=product.id,
                                      title=product.title,
                                      vendor=product.vendor,
                                      tags=product.tags,
                                      type=product.product_type,
                                      image=product.image.thumb if product.image else None) for product in products]
            Product.objects.bulk_create(product_models)
            cursor = shopify.ShopifyResource.connection.response.headers.get('Link')
            for _ in cursor.split(','):
                if _.find('next') > 0:
                    page_info = _.split(';')[0].strip('<>').split('page_info=')[1]
            print('chunk fetched: %s' % chunk)
            if cache != page_info:
                return get_products(page_info, chunk + 1, limit)
            return None

        tic = time()
        get_products(limit=limit)
        print('Products fetch took about %ss' % math.ceil((time() - tic)))

    def bulk_add_variants(self, limit=250):
        def get_variants(page_info='', chunk=1, limit=''):
            """Fetch variants recursively."""
            cache = page_info
            variants = shopify.Variant.find(limit=250, page_info=page_info)
            variant_models = [Variant(store=self._user,
                                      variant_id=variant.id,
                                      product_id=variant.product_id,
                                      title=variant.title,
                                      price=variant.price,
                                      sku=variant.sku.strip(),
                                      qty=variant.inventory_quantity,
                                      inventory_item_id=variant.inventory_item_id) for variant in variants]
            Variant.objects.bulk_create(variant_models)
            cursor = shopify.ShopifyResource.connection.response.headers.get('Link')
            for _ in cursor.split(','):
                if _.find('next') > 0:
                    page_info = _.split(';')[0].strip('<>').split('page_info=')[1]
            print('chunk fetched: %s' % chunk)
            if cache != page_info:
                return get_variants(page_info, chunk + 1, limit)
            return None

        tic = time()
        get_variants(limit=limit)
        print('Variants fetch took about %ss' % math.ceil((time() - tic)))

    def __str__(self):
        return "Shopify store: %s" % self._user.myshopify_domain
