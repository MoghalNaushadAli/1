from django import forms
from .models import Address, Order


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["full_name", "phone", "line1", "line2", "landmark", "city", "state", "pincode", "is_default"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "10-digit mobile number"}),
            "line1": forms.TextInput(attrs={"class": "form-control", "placeholder": "House no., Building, Street"}),
            "line2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Area, Colony (optional)"}),
            "landmark": forms.TextInput(attrs={"class": "form-control", "placeholder": "Landmark (optional)"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "State"}),
            "pincode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Pincode"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CheckoutForm(forms.Form):
    address = forms.ModelChoiceField(queryset=Address.objects.none(), widget=forms.RadioSelect, required=False)
    delivery_slot = forms.ChoiceField(
        choices=[
            ("Today, Evening (6 PM - 9 PM)", "Today, Evening (6 PM - 9 PM)"),
            ("Tomorrow, Morning (8 AM - 10 AM)", "Tomorrow, Morning (8 AM - 10 AM)"),
            ("Tomorrow, Afternoon (12 PM - 3 PM)", "Tomorrow, Afternoon (12 PM - 3 PM)"),
            ("Tomorrow, Evening (6 PM - 9 PM)", "Tomorrow, Evening (6 PM - 9 PM)"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    payment_method = forms.ChoiceField(choices=[], required=True)
    notes = forms.CharField(
        required=False, max_length=250,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Delivery instructions (optional)"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import PAYMENT_CHOICES
        self.fields["payment_method"].choices = PAYMENT_CHOICES
        self.fields["payment_method"].widget = forms.RadioSelect(choices=PAYMENT_CHOICES)
        if user is not None:
            self.fields["address"].queryset = Address.objects.filter(user=user)
