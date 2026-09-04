"""Store a clearly timestamped fallback of public workflow status."""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def capture():
    path=ROOT/'dist/status.json'
    data=json.loads(path.read_text()) if path.exists() else {}
    repo=os.environ.get('GITHUB_REPOSITORY','qliugithub/plant-epigenomics-weekly-digest')
    runs={}
    try:
        for name,file in [('weekly','weekly.yml'),('publish','publish.yml')]:
            req=urllib.request.Request(f'https://api.github.com/repos/{repo}/actions/workflows/{file}/runs?per_page=10',headers={'Accept':'application/vnd.github+json','User-Agent':'PlantDigest'})
            if os.environ.get('GITHUB_TOKEN'):req.add_header('Authorization','Bearer '+os.environ['GITHUB_TOKEN'])
            with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
            runs[name]=[{k:r.get(k) for k in ['id','status','conclusion','created_at','updated_at','html_url']} for r in result['workflow_runs']]
        data['runs']=runs;data['snapshot_at']=dt.datetime.now(dt.timezone.utc).isoformat()
    except Exception:
        print('Status snapshot unavailable; previous snapshot retained. Live status remains available in the browser.')
        return
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':capture()
