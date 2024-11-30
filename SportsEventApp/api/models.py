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

