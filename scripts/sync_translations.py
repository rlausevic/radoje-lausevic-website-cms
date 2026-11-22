"""Refresh editorial status after Save; build independently enforces the same hashes."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from i18n import all_records,sync_record

def sync(root=None):
 for path,data,records in all_records() if root is None else all_records(root):
  before=json.dumps(data,ensure_ascii=False)
  for item,key in records:sync_record(item,key)
  if json.dumps(data,ensure_ascii=False)!=before:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':sync()
