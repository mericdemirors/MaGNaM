from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(KanbanTask)
admin.site.register(KanbanTaskTag)
admin.site.register(KanbanTaskVote)
