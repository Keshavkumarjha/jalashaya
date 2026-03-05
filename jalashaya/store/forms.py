from django import forms
from django.core.validators import MinValueValidator

from .models import Branch, ContactMessage, CustomerAddress, Order, Product


from django import forms
from django.core.validators import MinValueValidator

from .models import Branch, ContactMessage, CustomerAddress, Order, Product


class OrderCreateForm(forms.ModelForm):

    product_id = forms.UUIDField(widget=forms.HiddenInput())
    selected_address = forms.ChoiceField(required=False)
    save_address = forms.BooleanField(required=False)

    quantity = forms.IntegerField(min_value=1, validators=[MinValueValidator(1)])

    # Address fields
    label = forms.CharField(required=False)
    address_line_1 = forms.CharField(required=False)
    address_line_2 = forms.CharField(required=False)
    landmark = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state_name = forms.CharField(required=False)
    postal_code = forms.CharField(required=False)
    country = forms.CharField(required=False)

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

        self.fields["customer_name"].widget.attrs.update({"class": "form-control", "placeholder": "Your full name"})
        self.fields["customer_email"].widget.attrs.update({"class": "form-control", "placeholder": "you@example.com"})
        self.fields["customer_mobile"].widget.attrs.update({"class": "form-control", "placeholder": "+91 9876543210"})
        self.fields["branch"].widget.attrs.update({"class": "form-control"})
        self.fields["quantity"].widget.attrs.update({"class": "form-control", "min": 1})
        self.fields["note"].widget.attrs.update(
            {"class": "form-control", "rows": 3, "placeholder": "Any special instructions"},
        )
        self.fields["delivery_address"].widget = forms.HiddenInput()
        self.fields["delivery_address"].required = False

        self.fields["selected_address"].choices = [("", "Add New Address")]

        for field_name, placeholder in [
            ("label", "Home / Office / Other"),
            ("address_line_1", "Flat / House no, Building, Street"),
            ("address_line_2", "Area (optional)"),
            ("landmark", "Landmark (optional)"),
            ("city", "City"),
            ("state_name", "State"),
            ("postal_code", "PIN code"),
            ("country", "Country"),
        ]:
            self.fields[field_name].widget.attrs.update({
                "class": "form-control",
                "placeholder": placeholder
            })

    def clean(self):
        cleaned_data = super().clean()

        product_id = cleaned_data.get("product_id")
        qty = cleaned_data.get("quantity") or 1
        selected_address = cleaned_data.get("selected_address")
        customer_email = cleaned_data.get("customer_email")

        if not product_id:
            raise forms.ValidationError("Product missing")

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise forms.ValidationError("Product not available")

        if product.track_inventory and product.stock_qty < qty:
            raise forms.ValidationError("Not enough stock available")

        chosen_address = None
        resolved_delivery_address = None

        if selected_address:
            try:
                chosen_address = CustomerAddress.objects.get(
                    id=selected_address,
                    customer_email__iexact=customer_email,
                    is_active=True
                )
                resolved_delivery_address = chosen_address.full_address
            except CustomerAddress.DoesNotExist:
                raise forms.ValidationError("Saved address not found")

        else:
            address_line_1 = cleaned_data.get("address_line_1")
            city = cleaned_data.get("city")
            postal_code = cleaned_data.get("postal_code")

            if not address_line_1 or not city or not postal_code:
                raise forms.ValidationError("Please complete address")

            resolved_delivery_address = ", ".join(filter(None, [
                cleaned_data.get("address_line_1"),
                cleaned_data.get("address_line_2"),
                cleaned_data.get("landmark"),
                cleaned_data.get("city"),
                cleaned_data.get("state_name"),
                cleaned_data.get("postal_code"),
                cleaned_data.get("country"),
            ]))

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
        cleaned_data["resolved_delivery_address"] = resolved_delivery_address

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
