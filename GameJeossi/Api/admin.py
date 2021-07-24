from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, ProfileCard, CardImage, CardCommunity, CardStreamer, CardGameName, Message


class AccountAdmin(UserAdmin):
    list_display = ('pk', 'email', 'username', 'date_joined', 'last_login', 'is_admin', 'is_staff')
    search_fields = ('pk', 'email', 'username',)
    readonly_fields = ('pk', 'date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(CardCommunity)
admin.site.register(CardStreamer)
admin.site.register(CardGameName)
admin.site.register(ProfileCard)
admin.site.register(CardImage)
admin.site.register(Message)

