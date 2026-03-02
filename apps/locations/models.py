from django.db import models


class Location(models.Model):
    """
    Reusable location model with geocoordinates for map integrations.
    Can be shared across Events and Organizations.
    """

    name = models.CharField(max_length=200, blank=True)  # e.g. "Google Campus"
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    is_virtual = models.BooleanField(default=False)
    virtual_url = models.URLField(blank=True)

    class Meta:
        ordering = ["city", "name"]

    def __str__(self) -> str:
        if self.is_virtual:
            return f"Virtual — {self.virtual_url}"
        return f"{self.name}, {self.city}, {self.country}"
