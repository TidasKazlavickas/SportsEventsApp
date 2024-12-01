from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=100, db_column='Name')
    age = models.CharField(max_length=255, db_column='Age')
    gender = models.CharField(max_length=10, db_column='Gender')

    class Meta:
        db_table = 'Group'

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(db_column='Name')
    required_participant_fields = models.CharField(db_column="Required_participant_fields")
    reglament_lt = models.CharField(db_column='Reglament_LT')
    reglament_en = models.CharField(db_column='Reglament_EN')
    registration_deadline = models.DateField(db_column='Registration_deadline', null=True, blank=True)
    payment_project_id = models.CharField(db_column='Payment_project_id', max_length=255, blank=True, null=True)
    payment_password = models.CharField(db_column='Payment_password', max_length=255, blank=True, null=True)
    event_result_link = models.CharField(db_column='Event_result_link', max_length=500, blank=True, null=True)


    class Meta:
        db_table = 'sports_event'

    def __str__(self):
        return self.name


class Distance(models.Model):
    name_lt = models.CharField(db_column='Name_LT')
    name_en = models.CharField(db_column='Name_EN')
    numbers = models.CharField(db_column='Numbers')
    special_numbers = models.CharField(db_column='Special_numbers')
    price = models.CharField(db_column='Price')
    price_extra = models.CharField(db_column='Price_extra')
    price_extra_date = models.DateField(db_column='Price_extra_date')
    if_race = models.BooleanField(db_column='If_race')
    race_participant_count = models.IntegerField(db_column='Race_participant_count')

    class Meta:
        db_table = 'Distance'



class EventDistanceAssociation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='Event_Id')
    distance = models.ForeignKey(Distance, on_delete=models.CASCADE, db_column='Distance_Id')

    class Meta:
        db_table = 'event_distance_association'

    def __str__(self):
        return f"{self.event.name} - {self.distance.name_lt}"

class Participant(models.Model):
    First_name = models.CharField(max_length=100)
    Last_name = models.CharField(max_length=100)
    Date_of_birth = models.DateField()
    Gender = models.CharField(max_length=10)
    Email = models.EmailField()
    Country = models.CharField(max_length=100)
    City = models.CharField(max_length=100)
    Club = models.CharField(max_length=100)
    Shirt_size = models.CharField(max_length=10)
    Phone_number = models.CharField(max_length=15)
    Comment = models.TextField(blank=True)
    If_paid = models.BooleanField(default=False)
    If_number_received = models.BooleanField(default=False)
    If_shirt_received = models.BooleanField(default=False)

    # Many-to-many relationships via custom association tables
    events = models.ManyToManyField(Event, through='EventParticipantAssociation')
    distances = models.ManyToManyField(Distance, through='DistanceParticipantAssociation')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'participant'  # Custom table name in the database


class EventParticipantAssociation(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="event_participations")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participant_associations")

    class Meta:
        db_table = 'event_participant_association'


class DistanceParticipantAssociation(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="distance_participations")
    distance = models.ForeignKey(Distance, on_delete=models.CASCADE, related_name="participant_associations")

    class Meta:
        db_table = 'distance_participant_association'