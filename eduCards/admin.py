from django.contrib import admin
from .models import CardsPage, Category, Card, CardComment, CardReaction, CardsPageAccessToken


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ('name', 'order', 'color')


class CardsPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'layout', 'created', 'last_modified', 'is_active')
    list_filter = ('is_active', 'layout', 'require_approval', 'created', 'created_by')
    filter_horizontal = ('shared_with',)
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
    list_display = ('title', 'category', 'created_by', 'author_name', 'is_approved', 'is_pinned', 'created')
    list_filter = ('is_approved', 'is_pinned', 'color', 'category__cards_page', 'created')
    search_fields = ('title', 'content', 'additional_info', 'author_name')
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


class CardCommentAdmin(admin.ModelAdmin):
    list_display = ('card', 'display_author', 'created')
    list_filter = ('card__category__cards_page', 'created')
    search_fields = ('text', 'author_name', 'user__username')


admin.site.register(CardsPage, CardsPageAdmin)
admin.site.register(CardComment, CardCommentAdmin)
admin.site.register(CardReaction)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(CardsPageAccessToken, CardsPageAccessTokenAdmin)

