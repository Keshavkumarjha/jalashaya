from django.db.models import Sum, Count
from django.views.decorators.http import require_GET
from django.shortcuts import render

from jalashaya.store.models import Category, Product



def _get_primary_image(product):
    primary = product.images.filter(is_primary=True).first()
    if primary:
        return primary.image_url
    first = product.images.first()
    return first.image_url if first else None


@require_GET
def home(request):
    # -------------------------
    # Categories (active only)
    # -------------------------
    categories = Category.objects.filter(
        is_active=True
    ).order_by("sort_order", "name")

    # -------------------------
    # Featured Product (Hero)
    # -------------------------
    featured_product = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("sort_order", "-created_at")
        .first()
    )

    featured_image = None
    featured_price = None

    if featured_product:
        featured_image = _get_primary_image(featured_product)
        featured_price = featured_product.price


    context = {
        "categories": categories,
        "featured_product": featured_product,
        "featured_image": featured_image,
        "featured_price": featured_price,
    
    }

    return render(request, "pages/home.html", context)
