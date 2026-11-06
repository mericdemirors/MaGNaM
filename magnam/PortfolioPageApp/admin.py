from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Portfolio)
admin.site.register(PortfolioTag)
admin.site.register(PortfolioLike)
admin.site.register(PortfolioComment)
admin.site.register(Work)
