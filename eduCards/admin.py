from django.contrib import admin
from .models import CardsPage, Category, Card, CardsPageAccessToken


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ('name', 'order', 'color')


class CardsPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created', 'is_active', 'order')
    list_filter = ('is_active', 'created', 'created_by')
    search_fields = ('title', 'description')
    readonly_fields = ('created', 'last_modified', 'created_by', 'last_modified_by')
    inlines = [CategoryInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class CardInline(admin.TabularInline):
    model = Card
    extra = 1
    fields = ('title', 'order', 'created_by')
    readonly_fields = ('created_by',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'cards_page', 'order', 'color')
    list_filter = ('cards_page',)
    search_fields = ('name', 'description')
    readonly_fields = ('created', 'last_modified')
    inlines = [CardInline]


class CardAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_by', 'created', 'order')
    list_filter = ('category__cards_page', 'category', 'created')
    search_fields = ('title', 'content', 'additional_info')
    readonly_fields = ('created', 'last_modified', 'created_by', 'last_modified_by')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class CardsPageAccessTokenAdmin(admin.ModelAdmin):
    list_display = ('cards_page', 'token', 'created_by', 'created', 'is_active')
    list_filter = ('cards_page', 'is_active', 'created')
    search_fields = ('token', 'cards_page__title', 'created_by__username')
    readonly_fields = ('created',)


admin.site.register(CardsPage, CardsPageAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(CardsPageAccessToken, CardsPageAccessTokenAdmin)

