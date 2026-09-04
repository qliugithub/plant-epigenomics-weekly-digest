import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from journal_club import validate,TRAITS
from refresh_resources import LANES
cards=json.loads(Path('data/journal_club.json').read_text())
assert cards and 'improvement' in LANES
for card in cards.values():
 validate(card)
 for mutation in [{'origin':'own_multiomics'},{'conservation':'confirmed'},{'traits':['standard_flowering']},{'en':{}}]:
  try:validate({**card,**mutation});raise AssertionError('Invalid proposal accepted')
  except ValueError:pass
validate(None)
print('PASS: bilingual proposal schema, trait vocabulary, unverified conservation and source scope.')
