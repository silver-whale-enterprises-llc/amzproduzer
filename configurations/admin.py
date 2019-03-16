from django.contrib import admin

from configurations.management.commands.get_categories import get_categories_from_keepa
from configurations.models import CategorySalesRank


class CategorySalesRankAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'max_allowed',
        'preferred',
    )

    actions = ['get_categories']

    def get_categories(self, request, queryset):
        get_categories_from_keepa()

    get_categories.short_description = "Get category ids from keepa"


admin.site.register(CategorySalesRank, CategorySalesRankAdmin)
