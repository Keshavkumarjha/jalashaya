from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .models import (
    Branch,
    Category,
    ContactMessage,
    Order,
    Product,
    ProductImage,
    State,
)


# ----------------------------
# Helpers
# ----------------------------
def _get_primary_image(product: Product):
    """
    Returns primary image url if exists else first image url else None
    """
    imgs = getattr(product, "images_all", None) or product.images.all()
    primary = next((i for i in imgs if i.is_primary), None)
    if primary:
        return primary.image_url
    first = next(iter(imgs), None)
    return first.image_url if first else None


def _calc_totals(product: Product, qty: int) -> tuple[Decimal, Decimal, Decimal]:
    """
    subtotal, delivery_fee, total
    Customize delivery fee as per your business rules.
    """
    qty = max(int(qty), 1)
    subtotal = (product.price * Decimal(qty)).quantize(Decimal("0.01"))

    # Example delivery fee rule:
    # Free delivery above 200 else 20
    delivery_fee = Decimal("0.00")
    if subtotal < Decimal("200.00"):
        delivery_fee = Decimal("20.00")

    total = (subtotal + delivery_fee).quantize(Decimal("0.01"))
    return subtotal, delivery_fee, total


# ----------------------------
# Pages
# ----------------------------
@require_GET
def home(request):
    # Show categories + featured products (sort_order low)
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all")
        )
        .order_by("sort_order", "-created_at")[:12]
    )

    for p in products:
        p.primary_image = _get_primary_image(p)

    return render(
        request,
        "pages/home.html",
        {"categories": categories, "products": products},
    )


@require_GET
def services(request):
    """
    Services page:
    - List products
    - Filter by category using ?category=<slug>
    """
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")

    category_slug = request.GET.get("category")
    products_qs = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all")
        )
        .order_by("sort_order", "-created_at")
    )

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products_qs = products_qs.filter(category=active_category)

    products = list(products_qs)
    for p in products:
        p.primary_image = _get_primary_image(p)

    # SEO meta (use category SEO if filtered else generic)
    seo = {
        "title": active_category.seo_title if active_category and active_category.seo_title else "Services",
        "description": active_category.seo_description if active_category else "",
        "no_index": active_category.no_index if active_category else False,
        "canonical": active_category.canonical_url if active_category else "",
    }

    return render(
        request,
        "pages/services.html",
        {
            "categories": categories,
            "active_category": active_category,
            "products": products,
            "seo": seo,
        },
    )


@require_GET
def category_detail(request, slug):
    """
    SEO category page: /category/<slug>/
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)

    products = (
        Product.objects.filter(is_active=True, category=category)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all")
        )
        .order_by("sort_order", "-created_at")
    )

    for p in products:
        p.primary_image = _get_primary_image(p)

    seo = {
        "title": category.seo_title or category.name,
        "description": category.seo_description or "",
        "keywords": category.seo_keywords or "",
        "no_index": category.no_index,
        "canonical": category.canonical_url or request.build_absolute_uri(),
    }

    return render(
        request,
        "pages/category_detail.html",
        {"category": category, "products": products, "seo": seo},
    )


@require_GET
def product_detail(request, slug):
    """
    SEO product page: /product/<slug>/
    """
    product = get_object_or_404(Product, slug=slug, is_active=True, category__is_active=True)

    images = list(product.images.order_by("-is_primary", "id"))
    product.primary_image = _get_primary_image(product)

    seo = {
        "title": product.seo_title or product.name,
        "description": product.seo_description or (product.description[:160] if product.description else ""),
        "keywords": product.seo_keywords or "",
        "no_index": product.no_index,
        "canonical": product.canonical_url or request.build_absolute_uri(),
    }

    return render(
        request,
        "pages/product_detail.html",
        {"product": product, "images": images, "seo": seo},
    )


@require_GET
def contact_page(request):
    states = State.objects.filter(is_active=True).order_by("name")
    return render(request, "pages/contactus.html", {"states": states})


# ----------------------------
# Forms / Actions
# ----------------------------
@require_http_methods(["POST"])
@transaction.atomic
def create_order(request):
    """
    Create order from modal form (POST).
    Expected POST fields:
    - customer_name, customer_email, customer_mobile
    - delivery_address, note
    - product_id (uuid), branch_id (int), quantity
    """
    try:
        product_id = request.POST.get("product_id")
        branch_id = request.POST.get("branch_id")
        qty = int(request.POST.get("quantity") or 1)

        customer_name = (request.POST.get("customer_name") or "").strip()
        customer_email = (request.POST.get("customer_email") or "").strip()
        customer_mobile = (request.POST.get("customer_mobile") or "").strip()
        delivery_address = (request.POST.get("delivery_address") or "").strip()
        note = (request.POST.get("note") or "").strip()

        if not customer_name:
            raise ValidationError("Customer name is required.")
        if not customer_email:
            raise ValidationError("Email is required.")
        if not customer_mobile:
            raise ValidationError("Mobile is required.")
        if not delivery_address:
            raise ValidationError("Delivery address is required.")

        product = get_object_or_404(Product, id=product_id, is_active=True)
        branch = get_object_or_404(Branch, id=branch_id, is_active=True)

        if qty < 1:
            qty = 1

        # Inventory check
        if product.track_inventory and product.stock_qty < qty:
            raise ValidationError("Not enough stock available.")

        subtotal, delivery_fee, total = _calc_totals(product, qty)

        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_mobile=customer_mobile,
            product=product,
            branch=branch,
            quantity=qty,
            delivery_address=delivery_address,
            note=note or None,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total,
            status="pending",
        )

        # Reduce stock (if tracked)
        if product.track_inventory:
            Product.objects.filter(id=product.id).update(stock_qty=models.F("stock_qty") - qty)

        messages.success(request, "Order placed successfully!")
        return redirect(reverse("services"))

    except ValidationError as e:
        messages.error(request, str(e))
        return redirect(reverse("services"))
    except Exception:
        messages.error(request, "Something went wrong while placing the order.")
        return redirect(reverse("services"))


@require_http_methods(["POST"])
def contact_submit(request):
    """
    Contact page POST submit
    """
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    subject = (request.POST.get("subject") or "").strip()
    message_text = (request.POST.get("message") or "").strip()

    if not name or not email or not subject or not message_text:
        messages.error(request, "All fields are required.")
        return redirect(reverse("contact"))

    ContactMessage.objects.create(
        name=name,
        email=email,
        subject=subject,
        message=message_text,
    )

    messages.success(request, "Thanks! We received your message.")
    return redirect(reverse("contact"))


# ----------------------------
# AJAX / JSON (Optional)
# ----------------------------
@require_GET
def branches_by_state(request):
    """
    /ajax/branches/?state_id=1
    returns: [{id, name}]
    """
    state_id = request.GET.get("state_id")
    if not state_id:
        return JsonResponse({"results": []})

    branches = Branch.objects.filter(state_id=state_id, is_active=True).order_by("name")
    data = [{"id": b.id, "name": b.name} for b in branches]
    return JsonResponse({"results": data})


@require_GET
def product_quick_info(request):
    """
    /ajax/product-info/?product_id=<uuid>
    returns: price, stock, image
    """
    product_id = request.GET.get("product_id")
    if not product_id:
        return JsonResponse({"error": "product_id required"}, status=400)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    image = _get_primary_image(product)

    return JsonResponse(
        {
            "id": str(product.id),
            "name": product.name,
            "price": str(product.price),
            "track_inventory": product.track_inventory,
            "stock_qty": product.stock_qty,
            "image_url": image,
        }
    )
