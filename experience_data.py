"""Shared work-experience dates, labels and stable chronological ordering."""
import datetime,re

MONTHS=('January','February','March','April','May','June','July','August','September','October','November','December')

def experience_date(value):
 if not value:return None
 if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?',value):raise ValueError('Invalid work-experience date: '+str(value))
 try:return datetime.date.fromisoformat(value+'-01' if len(value)==7 else value)
 except ValueError:raise ValueError('Invalid work-experience date: '+value)

def experience_period(item,language='en'):
 ongoing=item.get('ongoing',False)
 if not isinstance(ongoing,bool):raise ValueError('Radno iskustvo u toku must be true or false')
 start=experience_date(item.get('start'))
 end=None if ongoing else experience_date(item.get('end'))
 if start and end and end<start:raise ValueError('Work-experience end date precedes start date')
 months=('јануар','фебруар','март','април','мај','јун','јул','август','септембар','октобар','новембар','децембар') if language=='sr' else MONTHS
 label=lambda value:months[value.month-1]+' '+str(value.year)
 if language=='sr':
  if start and ongoing:return label(start)+' – данас'
  if start and end:return label(start)+' – '+label(end)
  if ongoing:return 'У току'
  if start:return 'Од '+label(start)
  if end:return 'До '+label(end)
 if start and ongoing:return label(start)+' - ongoing'
 if start and end:return label(start)+' - '+label(end)
 if ongoing:return 'Ongoing'
 if start:return 'From '+label(start)
 if end:return 'Until '+label(end)
 if not any(key in item for key in ['start','end','ongoing']):return item.get('period') or ''
 return ''

def experience_sort_key(item):
 ongoing=item.get('ongoing') is True
 try:date=experience_date(item.get('start' if ongoing else 'end'))
 except ValueError:date=None
 return (ongoing,date or datetime.date.min)
