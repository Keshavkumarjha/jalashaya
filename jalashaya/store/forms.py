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

        self.fields["customer_name"].widget.attrs.update({"class": "form-control", "placeholder": "Full name"})
        self.fields["customer_email"].widget.attrs.update({"class": "form-control", "placeholder": "Email"})
        self.fields["customer_mobile"].widget.attrs.update({"class": "form-control", "placeholder": "Mobile"})
        self.fields["branch"].widget.attrs.update({"class": "form-select"})
        self.fields["quantity"].widget.attrs.update({"class": "form-control", "min": 1})
        self.fields["delivery_address"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Delivery address", "rows": 2}
        )
        self.fields["note"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Order note (optional)", "rows": 2}
        )

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

        branch = cleaned_data.get("branch")
        if branch and not branch.is_active:
            raise forms.ValidationError("Selected branch is currently unavailable.")

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
        self.fields["message"].widget.attrs.update(
            {"class": "form-control", "rows": 5, "placeholder": "Write your message"}
        )
