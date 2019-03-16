from django.db import models

from abstracts.models import TimeStamp


class CategorySalesRank(TimeStamp):
    name = models.CharField(max_length=255, default='')
    max_allowed = models.IntegerField(null=False, blank=False, default=200000)
    preferred = models.IntegerField(null=False, blank=False, default=100000)

    def __str__(self):
        return f'<CategorySalesRank: {self.id}, {self.name}, {self.preferred}>'
