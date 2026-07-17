from django.core.exceptions import ValidationError
from django.db import models
from geopy.geocoders import Nominatim


class GeoFencing(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_in_meters = models.IntegerField()
    company_id = models.ForeignKey(
        "base.Company",
        related_name="geo_fencing",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    start = models.BooleanField(default=False)

    def clean(self):
        geolocator = Nominatim(
            user_agent="geo_checker_unique"
        )  # Unique user-agent is important
        if self.start:
            try:
                location = geolocator.reverse(
                    (self.latitude, self.longitude), exactly_one=True
                )
                if not location:
                    raise ValidationError("Invalid location coordinates.")
            except Exception as e:
                raise ValidationError(f"Geolocation error: {e}")

        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean before save
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Geofence #{self.pk}"
