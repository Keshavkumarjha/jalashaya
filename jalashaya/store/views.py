from decimal import Decimal
import json
import logging
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.db.models import F, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ContactMessageForm, OrderCreateForm
from .models import Branch, Category, CustomerAddress, Product, ProductImage

logger = logging.getLogger(__name__)


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


def _normalize_mobile_for_whatsapp(mobile: str | None) -> str | None:
    digits = "".join(ch for ch in (mobile or "") if ch.isdigit())
    if not digits:
        return None
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def _send_whatsapp_receipt(order):
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    template_name = getattr(settings, "WHATSAPP_TEMPLATE_NAME", "hello_world")

    if not token or not phone_number_id:
        return

    recipient = _normalize_mobile_for_whatsapp(order.customer_mobile)
    if not recipient:
        return

    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"},
        },
    }

    req = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=10):  # noqa: S310
            return
    except (urllib_error.URLError, TimeoutError, ValueError) as exc:
        logger.warning("WhatsApp receipt send failed for order %s: %s", order.id, exc)


@require_GET
def home(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all"),
        )
        .order_by("sort_order", "-created_at")[:8]
    )

    for product in products:
        product.primary_image = _get_primary_image(product)

    return render(request, "pages/home.html", {"categories": categories, "products": products})


@require_GET
def services(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    branches = Branch.objects.filter(is_active=True).select_related("state").order_by("state__name", "name")

    category_slug = request.GET.get("category")
    products_qs = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all"),
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
            "branches": branches,
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
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "id"), to_attr="images_all"),
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
    form = ContactMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks! We received your message.")
            return redirect(reverse("contact"))
        messages.error(request, "Please correct the errors below and submit again.")

    return render(request, "pages/contactus.html", {"form": form})


@require_http_methods(["POST"])
def contact_submit(request):
    form = ContactMessageForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks! We received your message.")
    else:
        messages.error(request, "Please correct the errors below and submit again.")
    return redirect(reverse("contact"))


@require_http_methods(["POST"])
@transaction.atomic
def create_order(request):
    form = OrderCreateForm(request.POST)

    if not form.is_valid():
        messages.error(request, form.errors.as_text())
        return redirect(reverse("services"))

    product = form.cleaned_data["product"]
    qty = form.cleaned_data["quantity"]
    subtotal, delivery_fee, total = _calc_totals(product, qty)

    chosen_address = form.cleaned_data.get("chosen_address")
    resolved_delivery_address = form.cleaned_data["resolved_delivery_address"]

    if not chosen_address and form.cleaned_data.get("save_address"):
        chosen_address = CustomerAddress.objects.create(
            customer_name=form.cleaned_data["customer_name"],
            customer_email=form.cleaned_data["customer_email"],
            customer_mobile=form.cleaned_data["customer_mobile"],
            label=(form.cleaned_data.get("address_label") or "Saved Address").strip() or "Saved Address",
            address_line_1=form.cleaned_data["address_line_1"],
            address_line_2=form.cleaned_data.get("address_line_2"),
            landmark=form.cleaned_data.get("landmark"),
            city=form.cleaned_data["city"],
            state_name=form.cleaned_data["state_name"],
            postal_code=form.cleaned_data["postal_code"],
            country=form.cleaned_data["country"],
            is_active=True,
        )

    order = OrderCreateForm.Meta.model.objects.create(
        customer_name=form.cleaned_data["customer_name"],
        customer_email=form.cleaned_data["customer_email"],
        customer_mobile=form.cleaned_data["customer_mobile"],
        product=product,
        branch=form.cleaned_data["branch"],
        customer_address=chosen_address,
        quantity=qty,
        delivery_address=resolved_delivery_address[:255],
        note=form.cleaned_data["note"],
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total,
        status="pending",
    )

    if product.track_inventory:
        Product.objects.filter(id=product.id).update(stock_qty=F("stock_qty") - qty)

    _send_whatsapp_receipt(order)

    messages.success(request, f"Order created successfully! Current status: {order.get_status_display()}.")
    return redirect(reverse("services"))


@require_GET
def customer_addresses(request):
    customer_email = request.GET.get("email", "").strip()
    if not customer_email:
        return JsonResponse({"results": []})

    addresses = CustomerAddress.objects.filter(customer_email__iexact=customer_email, is_active=True).order_by("-created_at")
    data = [
        {
            "id": addr.id,
            "label": addr.label or "Saved address",
            "address": addr.full_address,
            "address_line_1": addr.address_line_1,
            "address_line_2": addr.address_line_2,
            "landmark": addr.landmark,
            "city": addr.city,
            "state_name": addr.state_name,
            "postal_code": addr.postal_code,
            "country": addr.country,
        }
        for addr in addresses
    ]
    return JsonResponse({"results": data})


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
        },
    )
