from graphene_django import DjangoObjectType

from products.models import InventoryUpload, Product, Supplier, AmazonCategory, AmazonProductListing


class SupplierNode(DjangoObjectType):
    class Meta:
        model = Supplier


class InventoryUploadNode(DjangoObjectType):
    class Meta:
        model = InventoryUpload


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product


class AmazonCategoryNode(DjangoObjectType):
    class Meta:
        model = AmazonCategory


class AmazonProductListingNode(DjangoObjectType):
    class Meta:
        model = AmazonProductListing
