from django import forms
from django.core.validators import MinValueValidator

from .models import Branch, ContactMessage, Order, Product


class OrderCreateForm(forms.ModelForm):
    product_id = forms.UUIDField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, validators=[MinValueValidator(1)])

    class Meta:
        model = Order
        fields = [
            "customer_name",
            "customer_email",
            "customer_mobile",
            "branch",
            "quantity",
            "delivery_address",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].queryset = Branch.objects.filter(is_active=True).select_related("state")

    def clean(self):
        cleaned_data = super().clean()
        product_id = cleaned_data.get("product_id")
        qty = cleaned_data.get("quantity") or 1

        if not product_id:
            raise forms.ValidationError("Please select a product.")

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise forms.ValidationError("Selected product is not available.") from exc

        if product.track_inventory and product.stock_qty < qty:
            raise forms.ValidationError("Not enough stock available for this product.")

        cleaned_data["product"] = product
        return cleaned_data


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control", "placeholder": "Your name"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "you@example.com"})
        self.fields["subject"].widget.attrs.update({"class": "form-control", "placeholder": "Subject"})
        self.fields["message"].widget.attrs.update({"class": "form-control", "rows": 5, "placeholder": "Write your message"})
