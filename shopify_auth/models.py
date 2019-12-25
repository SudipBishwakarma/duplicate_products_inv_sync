from django.db import models


class ShopifyStore(models.Model):
    """Model representing shopify stores which have installed this app."""
    name = models.CharField(max_length=100, help_text='Shopify store name.', null=True, blank=True)
    myshopify_domain = models.CharField(max_length=100, help_text='Shopify store domain.', unique=True)
    email = models.EmailField(max_length=100, help_text='Store email address.', null=True, blank=True)
    shop_owner = models.CharField(max_length=100, help_text='Shopify store owner name.', null=True, blank=True)
    country_name = models.CharField(max_length=100, help_text='Store location.', null=True, blank=True)
    access_token = models.CharField(max_length=100, help_text='Permanent token received from shopify.', null=True, blank=True)
    date_installed = models.DateTimeField(help_text='App installation date.', null=True, blank=True)

    def __str__(self):
        """String representation for model object."""
        return self.name


class Product(models.Model):
    """Model representing products fetched from shopify store."""
    store = models.ForeignKey('ShopifyStore', on_delete=models.CASCADE, help_text='Shopify store id.')
    product_id = models.BigIntegerField(verbose_name='product ID', help_text='Shopify product id.')
    title = models.CharField(max_length=200, help_text='Product title', null=True, blank=True)
    vendor = models.CharField(max_length=200, help_text='Product vendor.', null=True, blank=True)
    tags = models.TextField(help_text='Product tags', null=True, blank=True)
    type = models.CharField(max_length=200, help_text='Product type', null=True, blank=True)
    image = models.CharField(max_length=300, help_text='Product image', null=True, blank=True)

    def __str__(self):
        """String representation for model object."""
        return self.title


class Variant(models.Model):
    """Model representing variant product belonging to the main product."""
    store = models.ForeignKey('ShopifyStore', on_delete=models.CASCADE, help_text='Shopify store id.')
    variant_id = models.BigIntegerField('variant ID', help_text='Variant product id.', null=True, blank=True)
    product_id = models.BigIntegerField('product ID', help_text='Parent product of variant.', null=True, blank=True)
    title = models.CharField(max_length=200, help_text='Variant title', null=True, blank=True)
    price = models.FloatField(help_text='Variant product price.', null=True, blank=True)
    sku = models.CharField(max_length=30, help_text='Variant SKU.', null=True, blank=True)
    qty = models.IntegerField(help_text='Variant quantity', null=True, blank=True)
    inventory_management = models.BooleanField(help_text='Inventory Managed', default=False, null=True, blank=True)
    inventory_item_id = models.BigIntegerField(help_text='Variant inventory item id', null=True, blank=True)

    def __str__(self):
        return self.title


# Not needed anymore.
class DuplicateManager(models.Manager):
    """Model Manager for duplicate variants."""
    def get_duplicates(self, store, start=0, end=25):
        _store = store.id
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f"""
            SELECT v.variant_id, p.image, p.title as p_title, v.sku, p.product_id, p.type, p.vendor, v.title as v_title
            FROM shopify_auth_product AS p JOIN shopify_auth_variant AS v ON p.product_id=v.product_id WHERE
            p.store_id={_store} AND sku IN (SELECT sku FROM shopify_auth_variant WHERE store_id={_store} GROUP BY sku
            HAVING COUNT(sku) > 1) ORDER BY v.variant_id LIMIT {start}, {end}""")
            result_list = []
            for row in cursor.fetchall():
                p = self.model(id=row[0],
                               image=row[1],
                               p_title=row[2],
                               sku=row[3],
                               product_id=row[4],
                               type=row[5],
                               vendor=row[6],
                               v_title=row[7])
                result_list.append(p)
            return result_list


class Duplicate(models.Model):
    """Model View representing duplicate variants from Product and Variant models."""
    image = models.CharField(max_length=300, help_text='Product image', null=True, blank=True)
    p_title = models.CharField(max_length=200, help_text='Product title', null=True, blank=True)
    sku = models.CharField(max_length=30, help_text='Variant SKU.', null=True, blank=True)
    product_id = models.BigIntegerField('product ID', help_text='Parent product of variant.', null=True, blank=True)
    type = models.CharField(max_length=200, help_text='Product type', null=True, blank=True)
    vendor = models.CharField(max_length=200, help_text='Product vendor.', null=True, blank=True)
    v_title = models.CharField(max_length=200, help_text='Variant title', null=True, blank=True)
    # objects = DuplicateManager()

    class Meta:
        managed = False
