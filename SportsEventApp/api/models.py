from django.db import models

# Grupės modelis
class Group(models.Model):
    name = models.CharField(max_length=100)
    year_from = models.IntegerField()
    year_to = models.IntegerField()
    gender_male = models.BooleanField(default=False)
    gender_female = models.BooleanField(default=False)
    sorting_number = models.IntegerField(default=0)

    def __str__(self):
        return self.name

# Renginio modelis
class Event(models.Model):
    title = models.CharField(max_length=200)
    required_fields = models.JSONField(default=list)  # Sąrašas pasirinkimų JSON formatu
    lt_regulations = models.URLField(null=True, blank=True)
    en_regulations = models.URLField(null=True, blank=True)
    registration_deadline = models.DateField()
    logo = models.ImageField(upload_to='event_logos/', null=True, blank=True)

    def __str__(self):
        return self.title

# Bėgimo distancijos modelis
class RaceDistance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='distances')
    name_lt = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, null=True, blank=True)
    groups = models.ManyToManyField(Group, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    additional_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name_lt} ({self.event.title})"
