import json
import os

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma as djintcomma
from django.utils.dateparse import parse_datetime

register = template.Library()


@register.filter
def jsonify(value):
    return json.dumps(value)


@register.filter
def intcomma(value):
    return djintcomma(value)


@register.simple_tag(takes_context=True)
def load_vaccine_stats(context, varname):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '../vaccine-stats.json'
    ))
    with open(path, 'r') as f:
        stats = json.loads(f.read())
        if 'updated' in stats:
            stats['updated'] = parse_datetime(stats['updated'])
        context[varname] = stats
    return ''
