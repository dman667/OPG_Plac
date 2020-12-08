from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

import OPG_Plac.models as models

# Register your models here.


class UserAdminConfig(UserAdmin):
    model = models.User
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('email', 'last_name', 'is_active', 'is_admin')
    ordering = ('-email', )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_admin')

    fieldsets = (
        (None, {'fields': ('email', 'first_name')}),
        ('Permissions', {'fields': ('is_active', 'is_admin')})
    )


admin.site.register([

    models.User,
    models.BlogArticle,
    models.BlogCategory,
    models.ProductCategory,
    models.ProductSubCategory,
    models.Product,
    models.ProductBrand,
    models.ProductAvailability

], UserAdminConfig)

