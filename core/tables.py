import django_tables2 as tables
from core.models import rfinv_inv

class rfinv_invHTMxTable(tables.Table):
    class Meta:
        model = rfinv_inv
        template_name = "tables/bootstrap_htmx.html"