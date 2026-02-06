from django.contrib import admin
from django.utils.html import format_html
from django.utils.text import Truncator

from django.contrib.auth.models import Group

from .models import (
    State,
    Branch,
    Category,
    Product,
    ProductImage,
    Order,
    ContactMessage,
)

# -------------------------------------------------
# GLOBAL ADMIN BRANDING
# -------------------------------------------------
admin.site.site_header = "Jalashaya Administration"
admin.site.site_title = "Jalashaya Admin Portal"
admin.site.index_title = "Water Supply Management Dashboard"


# -------------------------------------------------
# STATE ADMIN
# -------------------------------------------------
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("State Information", {"fields": ("name", "code", "is_active")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )


# -------------------------------------------------
# BRANCH ADMIN
# -------------------------------------------------
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "phone", "is_active")
    list_filter = ("state", "is_active")
    search_fields = ("name", "state__name", "phone")
    autocomplete_fields = ("state",)
    ordering = ("state__name", "name")

    fieldsets = (
        ("Branch Details", {"fields": ("state", "name", "address", "phone")}),
        ("Status", {"fields": ("is_active",)}),
    )


# -------------------------------------------------
# CATEGORY ADMIN
# -------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
    ordering = ("sort_order", "name")

    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "sort_order", "is_active")}),
        ("SEO Settings", {
            "classes": ("collapse",),
            "fields": (
                "seo_title",
                "seo_description",
                "seo_keywords",
                "canonical_url",
                "no_index",
            ),
        }),
        ("Audit", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


# -------------------------------------------------
# PRODUCT IMAGE INLINE
# -------------------------------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image_url", "alt_text", "is_primary")
    autocomplete_fields = ("product",)


# -------------------------------------------------
# PRODUCT ADMIN
# -------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "stock_status",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "sku", "category__name", "slug")
    autocomplete_fields = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)
    inlines = (ProductImageInline,)
    date_hierarchy = "created_at"

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Product Info", {
            "fields": (
                "category",
                "name",
                "slug",
                "sku",
                "badge_text",
                "description",
            )
        }),
        ("Pricing & Inventory", {
            "fields": (
                "price",
                "track_inventory",
                "stock_qty",
                "sort_order",
                "is_active",
            )
        }),
        ("SEO Settings", {
            "classes": ("collapse",),
            "fields": (
                "seo_title",
                "seo_description",
                "seo_keywords",
                "canonical_url",
                "no_index",
            ),
        }),
        ("Audit", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    actions = ("mark_active", "mark_inactive")

    @admin.display(description="Stock")
    def stock_status(self, obj):
        if not obj.track_inventory:
            return format_html("<span style='color:green;font-weight:700'>∞</span>")
        if obj.stock_qty > 0:
            return format_html("<b>{}</b>", obj.stock_qty)
        return format_html("<span style='color:red;font-weight:700'>Out</span>")

    @admin.action(description="Mark selected products as ACTIVE")
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) marked ACTIVE.")

    @admin.action(description="Mark selected products as INACTIVE")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) marked INACTIVE.")


# -------------------------------------------------
# ORDER ADMIN
# -------------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "customer_name",
        "customer_mobile",
        "product",
        "branch",
        "quantity",
        "formatted_total",
        "status_badge",
        "created_at",
    )

    list_filter = ("status", "branch", "created_at")
    search_fields = ("customer_name", "customer_email", "customer_mobile")
    autocomplete_fields = ("product", "branch")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("product", "branch")

    readonly_fields = (
        "subtotal",
        "delivery_fee",
        "total_amount",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Customer Info", {
            "fields": (
                "customer_name",
                "customer_email",
                "customer_mobile",
                "delivery_address",
                "note",
            )
        }),
        ("Order Details", {
            "fields": (
                "product",
                "branch",
                "quantity",
                "status",
            )
        }),
        ("Amounts", {
            "fields": (
                "subtotal",
                "delivery_fee",
                "total_amount",
            )
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    actions = ("mark_confirmed", "mark_processing", "mark_delivered", "mark_cancelled")

    @admin.display(description="Order ID")
    def short_id(self, obj):
        return str(obj.id).split("-")[0]

    @admin.display(description="Total")
    def formatted_total(self, obj):
        return f"₹ {obj.total_amount}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        color_map = {
            "pending": "#ffc107",
            "confirmed": "#0d6efd",
            "processing": "#0dcaf0",
            "delivered": "#198754",
            "cancelled": "#dc3545",
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="padding:4px 10px;color:#fff;background:{};border-radius:14px;font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Mark selected orders as Confirmed")
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status="confirmed")
        self.message_user(request, f"{updated} order(s) marked CONFIRMED.")

    @admin.action(description="Mark selected orders as Processing")
    def mark_processing(self, request, queryset):
        updated = queryset.update(status="processing")
        self.message_user(request, f"{updated} order(s) marked PROCESSING.")

    @admin.action(description="Mark selected orders as Delivered")
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status="delivered")
        self.message_user(request, f"{updated} order(s) marked DELIVERED.")

    @admin.action(description="Mark selected orders as Cancelled")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} order(s) marked CANCELLED.")

    def has_delete_permission(self, request, obj=None):
        return False  # safer for production


# -------------------------------------------------
# CONTACT MESSAGE ADMIN (READ ONLY)
# -------------------------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "short_subject", "created_at")
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = ("name", "email", "subject", "message", "created_at", "updated_at")

    fieldsets = (
        ("Sender Info", {"fields": ("name", "email")}),
        ("Message", {"fields": ("subject", "message")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Subject")
    def short_subject(self, obj):
        return Truncator(obj.subject).chars(40)

    def has_add_permission(self, request):
        return False  # only from site form


# -------------------------------------------------
# REMOVE UNUSED DEFAULT MODELS
# -------------------------------------------------
admin.site.unregister(Group)
