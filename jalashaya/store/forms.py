from django import forms
from django.core.validators import MinValueValidator

from .models import Branch, ContactMessage, CustomerAddress, Order, Product


class OrderCreateForm(forms.ModelForm):
    product_id = forms.UUIDField(widget=forms.HiddenInput())
    selected_address = forms.ChoiceField(required=False)
    save_address = forms.BooleanField(required=False)
    address_label = forms.CharField(required=False, max_length=80)
    address_line_1 = forms.CharField(required=False, max_length=255)
    address_line_2 = forms.CharField(required=False, max_length=255)
    landmark = forms.CharField(required=False, max_length=200)
    city = forms.CharField(required=False, max_length=100)
    state_name = forms.CharField(required=False, max_length=100)
    postal_code = forms.CharField(required=False, max_length=12)
    country = forms.CharField(required=False, max_length=80, initial="India")
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
        if "branch" in self.fields:
            self.fields["branch"].queryset = Branch.objects.filter(is_active=True).select_related("state")

        for field_name, attrs in [
            ("customer_name", {"class": "form-control", "placeholder": "Your full name"}),
            ("customer_email", {"class": "form-control", "placeholder": "you@example.com"}),
            ("customer_mobile", {"class": "form-control", "placeholder": "+91 9876543210"}),
            ("branch", {"class": "form-control"}),
            ("quantity", {"class": "form-control", "min": 1}),
            ("note", {"class": "form-control", "rows": 3, "placeholder": "Any special instructions"}),
        ]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(attrs)

        if "delivery_address" in self.fields:
            self.fields["delivery_address"].widget = forms.HiddenInput()
            self.fields["delivery_address"].required = False

        if "selected_address" in self.fields:
            self.fields["selected_address"].widget.attrs.update({"class": "form-control", "id": "id_selected_address"})
            self.fields["selected_address"].choices = [("", "Add New Address")]

        if "save_address" in self.fields:
            self.fields["save_address"].widget.attrs.update({"id": "id_save_address"})

        for field_name, placeholder in [
            ("address_label", "Home / Office / Other"),
            ("address_line_1", "Flat / House no, Building, Street"),
            ("address_line_2", "Area (optional)"),
            ("landmark", "Landmark (optional)"),
            ("city", "City"),
            ("state_name", "State"),
            ("postal_code", "PIN code"),
            ("country", "Country"),
        ]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({"class": "form-control", "placeholder": placeholder})

    def clean(self):
        cleaned_data = super().clean()
        product_id = cleaned_data.get("product_id")
        qty = cleaned_data.get("quantity") or 1
        selected_address = cleaned_data.get("selected_address")
        customer_email = cleaned_data.get("customer_email")

        if not product_id:
            raise forms.ValidationError("Please select a product.")

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise forms.ValidationError("Selected product is not available.") from exc

        if product.track_inventory and product.stock_qty < qty:
            raise forms.ValidationError("Not enough stock available for this product.")

        chosen_address = None
        if selected_address:
            if not str(selected_address).isdigit():
                raise forms.ValidationError("Please select a valid saved address.")
            try:
                chosen_address = CustomerAddress.objects.get(
                    id=int(selected_address),
                    is_active=True,
                    customer_email__iexact=customer_email,
                )
            except CustomerAddress.DoesNotExist as exc:
                raise forms.ValidationError("Saved address not found.") from exc
        else:
            required_new_fields = ["address_line_1", "city", "state_name", "postal_code", "country"]
            missing = [name for name in required_new_fields if not (cleaned_data.get(name) or "").strip()]
            if missing:
                raise forms.ValidationError("Please fill complete new address details.")

        if chosen_address:
            cleaned_data["resolved_delivery_address"] = chosen_address.full_address
        else:
            line_1 = (cleaned_data.get("address_line_1") or "").strip()
            line_2 = (cleaned_data.get("address_line_2") or "").strip()
            landmark = (cleaned_data.get("landmark") or "").strip()
            city = (cleaned_data.get("city") or "").strip()
            state_name = (cleaned_data.get("state_name") or "").strip()
            postal_code = (cleaned_data.get("postal_code") or "").strip()
            country = (cleaned_data.get("country") or "").strip()
            cleaned_data["resolved_delivery_address"] = ", ".join(
                [part for part in [line_1, line_2, landmark, city, state_name, postal_code, country] if part],
            )

        cleaned_data["product"] = product
        cleaned_data["chosen_address"] = chosen_address
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
