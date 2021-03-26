import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from django.template.loader import add_to_builtins
add_to_builtins('plugins.template_tags')
