from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CaseInsensitiveFieldMixin:
    """
    Field mixin that uses case-insensitive lookup alternatives if they exist.
    """

    LOOKUP_CONVERSIONS = {
        "exact": "iexact",
        "contains": "icontains",
        "startswith": "istartswith",
        "endswith": "iendswith",
        "regex": "iregex",
    }

    def get_lookup(self, lookup_name):
        converted = self.LOOKUP_CONVERSIONS.get(lookup_name, lookup_name)
        return super().get_lookup(converted)


class CICharField(CaseInsensitiveFieldMixin, models.CharField):
    pass


class Car(models.Model):
    class Meta:
        ordering = ["pk"]
        unique_together = ("make", "model")

    make = CICharField(max_length=20)
    model = CICharField(max_length=20)

    @property
    def avg_rate(self):
        votes = self.votes_cnt
        score = CarRate.objects.filter(car_id=self.pk).aggregate(models.Sum("rate"))[
            "rate__sum"
        ]
        return round(score / votes, 2) if votes and score else None

    @property
    def votes_cnt(self):
        return CarRate.objects.filter(car_id=self.pk).count()

    def __str__(self):
        return self.make, self.model


class CarRate(models.Model):
    car_id = models.ForeignKey(Car, on_delete=models.CASCADE)
    rate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
