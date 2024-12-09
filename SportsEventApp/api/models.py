from datetime import date

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
    event_date = models.DateField(db_column='Event_date', null=True, blank=True)
    class Meta:
        db_table = 'sports_event'

    def __str__(self):
        return self.name


class Distance(models.Model):
    name_lt = models.CharField(db_column='Name_LT', max_length=255)
    name_en = models.CharField(db_column='Name_EN', max_length=255)
    numbers = models.CharField(db_column='Numbers', max_length=255)
    special_numbers = models.CharField(db_column='Special_numbers', max_length=255)
    price = models.CharField(db_column='Price', max_length=255)
    price_extra = models.CharField(db_column='Price_extra', max_length=255)
    price_extra_date = models.DateField(db_column='Price_extra_date')
    if_race = models.BooleanField(db_column='If_race')
    race_participant_count = models.IntegerField(db_column='Race_participant_count')

    groups = models.ManyToManyField(Group, through='DistanceGroupAssociation')
    class Meta:
        db_table = 'Distance'

    def __str__(self):
        return self.name_lt



class EventDistanceAssociation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='Event_Id')
    distance = models.ForeignKey(Distance, on_delete=models.CASCADE, db_column='Distance_Id')

    class Meta:
        db_table = 'event_distance_association'

    def __str__(self):
        return f"{self.event.name} - {self.distance.name_lt}"

class Participant(models.Model):
    first_name = models.CharField(max_length=100, db_column='First_name')
    last_name = models.CharField(max_length=100, db_column='Last_name')
    date_of_birth = models.DateField(db_column='Date_of_birth')
    gender = models.CharField(max_length=10, db_column='Gender')
    email = models.EmailField(db_column='Email')
    country = models.CharField(max_length=100, db_column='Country')
    city = models.CharField(max_length=100, db_column='City')
    club = models.CharField(max_length=100, db_column='Club')
    shirt_size = models.CharField(max_length=10, db_column='Shirt_size')
    phone_number = models.CharField(max_length=15, db_column='Phone_number')
    comment = models.TextField(blank=True, db_column='Comment')
    if_paid = models.BooleanField(default=False, db_column='If_paid')
    if_number_received = models.BooleanField(default=False, db_column='If_number_received')
    if_shirt_received = models.BooleanField(default=False, db_column='If_shirt_received')
    registration_date = models.DateField(auto_now_add=True, db_column='Registration_date')
    shirt_number = models.IntegerField(db_column='Shirt_number')

    # Many-to-many relationships via custom association tables
    events = models.ManyToManyField(Event, through='EventParticipantAssociation')
    distances = models.ManyToManyField(Distance, through='DistanceParticipantAssociation')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'participant'

    def calculate_payment(self):
            today = date.today()
            distance = self.distances.first()
            price = float(distance.price)  # Assuming price is stored as a string
            price_extra = float(distance.price_extra)
            price_extra_date = distance.price_extra_date

            # If the current date is after the price_extra_date, add the extra price
            if today >= price_extra_date:
                price = price_extra

            total_payment = price

            return total_payment


class EventParticipantAssociation(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="event_participations", db_column='Participant_Id')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participant_associations", db_column='Event_Id')

    class Meta:
        db_table = 'event_participant_association'


class DistanceParticipantAssociation(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="distance_participations")
    distance = models.ForeignKey(Distance, on_delete=models.CASCADE, related_name="participant_associations")

    class Meta:
        db_table = 'distance_participant_association'

class DistanceGroupAssociation(models.Model):
    distance = models.ForeignKey(Distance, on_delete=models.CASCADE, related_name="group_distances", db_column='Distance_Id')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_associations', db_column='Group_Id')

    class Meta:
        db_table = 'distance_group_association'

class GroupParticipantAssociation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='participant_groups', db_column="Group_Id")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='participant_associations', db_column='Participant_Id')

    class Meta:
        db_table = 'group_participant_association'