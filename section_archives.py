"""Small in-page archives: shared controls, accessible paging and no-JS fallback."""
from html import escape
import datetime
E=lambda value:escape(str(value),quote=True)

def date_label(value):
 try:return datetime.date.fromisoformat(str(value)[:10]).strftime('%b %d, %Y')
 except ValueError:return ''

def controls(prefix,label,years,categories=()):
 out=f'<div class="filters journal-filters" data-section-controls><label for="{prefix}-search">{label}<input type="search" id="{prefix}-search" data-section-search placeholder="{label}…" aria-controls="{prefix}-results"></label>'
 if categories:out+=f'<label for="{prefix}-category">Category<select id="{prefix}-category" data-section-category><option value="">All categories</option>'+''.join(f'<option value="{E(c)}">{E(c)}</option>' for c in categories)+'</select></label>'
 out+=f'<label for="{prefix}-year">Year<select id="{prefix}-year" data-section-year><option value="">All years</option>'+''.join(f'<option value="{E(y)}">{E(y)}</option>' for y in sorted(set(years)-{'undated'},reverse=True))
 if 'undated' in years:out+='<option value="undated">Undated</option>'
 return out+'</select></label></div>'

def paging(prefix,group,label,total,size):
 end=min(size,total)
 if total==1:label=label.removesuffix('s')
 text=f'Showing 1–{end} of {total} {label}' if total else f'0 {label}'
 return f'<p class="result-count" data-section-count role="status" aria-live="polite" tabindex="-1">{text}</p><nav class="journal-pagination" data-section-pagination aria-label="{E(group if prefix=='bibliography' else label)} pages" hidden></nav>'

def fallback(prefix):
 return f'<noscript><style>#{prefix}-archive [data-section-entry][hidden]{{display:revert!important}}#{prefix}-archive [data-section-controls],#{prefix}-archive [data-section-count],#{prefix}-archive [data-section-total]{{display:none}}</style><p>All entries are shown. Enable JavaScript to search, filter or browse numbered pages.</p></noscript>'
