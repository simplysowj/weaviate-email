from django.contrib import admin
from .models import EmailCampaign, Recipient, GeneratedEmail
from .models import EmailReply

admin.site.register(EmailReply)

class RecipientInline(admin.TabularInline):
    model = Recipient
    extra = 1

class GeneratedEmailInline(admin.StackedInline):
    model = GeneratedEmail
    can_delete = False
    verbose_name_plural = 'Generated Email'  # Fixed: Removed extra equals sign
    readonly_fields = ('generated_at',)

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name',  'topic', 'created_at')
    
    search_fields = ('name', 'topic')
    inlines = [RecipientInline, GeneratedEmailInline]
    fieldsets = (
        (None, {'fields': ( 'name', 'topic')}),
        ('Content', {'fields': ('details', 'tone')}),
    )

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'campaign', 'is_sent', 'sent_at')
    list_filter = ('is_sent', 'campaign')
    search_fields = ('email', 'name')

@admin.register(GeneratedEmail)
class GeneratedEmailAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'generated_at')
    readonly_fields = ('generated_at',)