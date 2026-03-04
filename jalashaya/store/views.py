from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import F, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ContactMessageForm, OrderCreateForm
from .models import Branch, Category, Order, Product, ProductImage, State


def _get_primary_image(product: Product):
    imgs = getattr(product, "images_all", None) or product.images.all()
    primary = next((i for i in imgs if i.is_primary), None)
    if primary:
        return primary.image_url
    first = next(iter(imgs), None)
    return first.image_url if first else None


def _calc_totals(product: Product, qty: int) -> tuple[Decimal, Decimal, Decimal]:
    qty = max(int(qty), 1)
    subtotal = (product.price * Decimal(qty)).quantize(Decimal("0.01"))
    delivery_fee = Decimal("0.00") if subtotal >= Decimal("200.00") else Decimal("20.00")
    total = (subtotal + delivery_fee).quantize(Decimal("0.01"))
    return subtotal, delivery_fee, total


@require_GET
def home(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all")
        )
        .order_by("sort_order", "-created_at")[:8]
    )

    for product in products:
        product.primary_image = _get_primary_image(product)

    return render(request, "pages/home.html", {"categories": categories, "products": products})


@require_GET
def services(request):
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
    for product in products:
        product.primary_image = _get_primary_image(product)

    return render(
        request,
        "pages/services.html",
        {
            "categories": categories,
            "active_category": active_category,
            "products": products,
            "order_form": OrderCreateForm(),
        },
    )


@require_GET
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = (
        Product.objects.filter(is_active=True, category=category)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all")
        )
        .order_by("sort_order", "-created_at")
    )

    for product in products:
        product.primary_image = _get_primary_image(product)

    return render(request, "pages/category_detail.html", {"category": category, "products": products})


@require_GET
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True, category__is_active=True)
    images = list(product.images.order_by("-is_primary", "id"))
    product.primary_image = _get_primary_image(product)
    return render(request, "pages/product_detail.html", {"product": product, "images": images})


@require_http_methods(["GET", "POST"])
def contact_page(request):
    states = State.objects.filter(is_active=True).order_by("name")
    form = ContactMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks! We received your message.")
            return redirect(reverse("contact"))
        messages.error(request, "Please correct the errors below and submit again.")

    return render(request, "pages/contactus.html", {"states": states, "form": form})


@require_http_methods(["POST"])
@transaction.atomic
def create_order(request):
    form = OrderCreateForm(request.POST)

    if not form.is_valid():
        first_error = next(iter(form.non_field_errors()), None)
        if not first_error:
            for errors in form.errors.values():
                if errors:
                    first_error = errors[0]
                    break
        messages.error(request, first_error or "Unable to place order. Please verify your details.")
        return redirect(reverse("services"))

    product = form.cleaned_data["product"]
    qty = form.cleaned_data["quantity"]
    subtotal, delivery_fee, total = _calc_totals(product, qty)

    Order.objects.create(
        customer_name=form.cleaned_data["customer_name"],
        customer_email=form.cleaned_data["customer_email"],
        customer_mobile=form.cleaned_data["customer_mobile"],
        product=product,
        branch=form.cleaned_data["branch"],
        quantity=qty,
        delivery_address=form.cleaned_data["delivery_address"],
        note=form.cleaned_data["note"],
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total,
        status="pending",
    )

    if product.track_inventory:
        Product.objects.filter(id=product.id).update(stock_qty=F("stock_qty") - qty)

    messages.success(request, "Order placed successfully! Our team will call you shortly.")
    return redirect(reverse("services"))


@require_GET
def branches_by_state(request):
    state_id = request.GET.get("state_id")
    if not state_id:
        return JsonResponse({"results": []})

    branches = Branch.objects.filter(state_id=state_id, is_active=True).order_by("name")
    data = [{"id": branch.id, "name": branch.name} for branch in branches]
    return JsonResponse({"results": data})


@require_GET
def product_quick_info(request):
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
