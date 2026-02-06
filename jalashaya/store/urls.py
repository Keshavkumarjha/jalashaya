from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact_page, name="contact"),
    path("contact/submit/", views.contact_submit, name="contact_submit"),

    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    path("order/create/", views.create_order, name="create_order"),

    # AJAX
    path("ajax/branches/", views.branches_by_state, name="branches_by_state"),
    path("ajax/product-info/", views.product_quick_info, name="product_quick_info"),
]
