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
        self.fields["customer_name"].widget.attrs.update({"class": "form-control", "placeholder": "Your full name"})
        self.fields["customer_email"].widget.attrs.update({"class": "form-control", "placeholder": "you@example.com"})
        self.fields["customer_mobile"].widget.attrs.update({"class": "form-control", "placeholder": "+91 9876543210"})
        self.fields["branch"].widget.attrs.update({"class": "form-control"})
        self.fields["quantity"].widget.attrs.update({"class": "form-control", "min": 1})
        self.fields["delivery_address"].widget.attrs.update({"class": "form-control", "placeholder": "Complete delivery address"})
        self.fields["note"].widget.attrs.update({"class": "form-control", "rows": 3, "placeholder": "Any special instructions"})

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
        fields = ["first_name", "last_name", "email", "phone", "city", "subject", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "First name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Last name"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "you@example.com"})
        self.fields["phone"].widget.attrs.update({"class": "form-control", "placeholder": "+91 9876543210"})
        self.fields["city"].widget.attrs.update({"class": "form-control", "placeholder": "Your city"})
        self.fields["subject"].widget.attrs.update({"class": "form-control", "placeholder": "Subject"})
        self.fields["message"].widget.attrs.update({"class": "form-control", "rows": 5, "placeholder": "Write your message"})
