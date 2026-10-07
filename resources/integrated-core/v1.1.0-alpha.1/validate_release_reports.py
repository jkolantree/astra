"""Check this stage's three reports through the unchanged bounded validators."""
from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'resources/integrated-edition-proposal')]
from validate_reports import validate
validate(*(json.loads((P/'generated'/n).read_text()) for n in ['integrated-case.json','scm-checks.json','wki-checks.json']))
print('PASS: bounded integration/SCM/WKI reports; no empirical admission')
