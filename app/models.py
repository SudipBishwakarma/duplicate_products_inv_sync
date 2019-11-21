from django.db import models
from shopify_auth.models import ShopifyStore


class FirstRun(models.Model):
    myshopify_domain = models.CharField(max_length=100, help_text='Shopify store domain.', unique=True)
    status = models.BooleanField(default=True, help_text='True if its the first visit, else False')
    bg_task = models.BooleanField(default=True, help_text='Background task running or completed.')

    def __str__(self):
        return self.status


class Preferences(models.Model):
    store = models.OneToOneField(ShopifyStore, on_delete=models.CASCADE, help_text='Store id.')
    activate = models.BooleanField(default=True, help_text='Enable or disable app.')
    tags = models.TextField(default='', help_text='Include listed tags')

    def __str__(self):
        return 'App status: %s' % self.activate
