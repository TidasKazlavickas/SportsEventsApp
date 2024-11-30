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
    id = models.IntegerField(db_column="Id", primary_key=True)
    name = models.CharField(db_column='Name')
    required_participant_fields = models.CharField(db_column="Required_participant_fields")
    reglament_lt = models.CharField(db_column='Reglament_LT')
    reglament_en = models.CharField(db_column='Reglament_EN')

    class Meta:
        db_table = 'sports_event'
