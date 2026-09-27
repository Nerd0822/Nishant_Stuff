from django import forms


class PlaceForm(forms.Form):
    destination = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Destination (optional)"}),
    )

    start_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Starting point (optional)"}),
    )

    # Filled by the "use my location" button in map.js
    start_lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    start_lon = forms.FloatField(required=False, widget=forms.HiddenInput())

    def clean_destination(self):
        value = self.cleaned_data["destination"]
        if not value:
            return value
        if value.isdigit():
            raise forms.ValidationError("please enter a place name")
        return value

    def clean_start_lat(self):
        value = self.cleaned_data.get("start_lat")
        if value is not None and not (-90 <= value <= 90):
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return value

    def clean_start_lon(self):
        value = self.cleaned_data.get("start_lon")
        if value is not None and not (-180 <= value <= 180):
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        destination = cleaned_data.get("destination") or ""
        start_location = cleaned_data.get("start_location") or ""
        start_lat = cleaned_data.get("start_lat")
        start_lon = cleaned_data.get("start_lon")
        has_start = bool(start_location) or (
            start_lat is not None and start_lon is not None
        )
        if not destination and not has_start:
            raise forms.ValidationError(
                "Enter a starting point or a destination."
            )
        return cleaned_data
