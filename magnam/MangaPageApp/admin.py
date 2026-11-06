from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Manga)
admin.site.register(MangaTag)
admin.site.register(MangaRating)
admin.site.register(MangaComment)
admin.site.register(Chapter)
admin.site.register(BoughtChapter)
admin.site.register(ReadChapter)
admin.site.register(MangaBookmark)