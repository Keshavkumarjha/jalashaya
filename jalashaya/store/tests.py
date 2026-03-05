from django.test import TestCase
from django.urls import reverse

from .models import Branch, Category, ContactMessage, CustomerAddress, Order, Product, State


class StoreFlowTests(TestCase):
    def setUp(self):
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.branch = Branch.objects.create(state=self.state, name="Bengaluru", is_active=True)
        self.category = Category.objects.create(name="Jar Water")
        self.product = Product.objects.create(
            category=self.category,
            name="20L Can",
            sku="CAN20",
            price="80.00",
            track_inventory=True,
            stock_qty=10,
            is_active=True,
        )

    def test_create_order_success(self):
        response = self.client.post(
            reverse("create_order"),
            {
                "product_id": str(self.product.id),
                "customer_name": "Rahul",
                "customer_email": "rahul@example.com",
                "customer_mobile": "9999999999",
                "branch": self.branch.id,
                "quantity": 2,
                "delivery_address": "MG Road",
                "note": "Ring bell",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_amount, order.subtotal + order.delivery_fee)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 8)

    def test_create_order_fails_when_insufficient_stock(self):
        response = self.client.post(
            reverse("create_order"),
            {
                "product_id": str(self.product.id),
                "customer_name": "Rahul",
                "customer_email": "rahul@example.com",
                "customer_mobile": "9999999999",
                "branch": self.branch.id,
                "quantity": 50,
                "delivery_address": "MG Road",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_contact_submit(self):
        response = self.client.post(
            reverse("contact"),
            {
                "first_name": "Asha",
                "last_name": "Sharma",
                "email": "asha@example.com",
                "phone": "9999999999",
                "city": "Bengaluru",
                "subject": "Bulk order",
                "message": "Need monthly water supply",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_create_order_saves_address_when_requested(self):
        response = self.client.post(
            reverse("create_order"),
            {
                "product_id": str(self.product.id),
                "customer_name": "Rahul",
                "customer_email": "rahul@example.com",
                "customer_mobile": "9999999999",
                "branch": self.branch.id,
                "quantity": 1,
                "delivery_address": "MG Road",
                "save_address": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomerAddress.objects.count(), 1)
