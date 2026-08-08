from pathlib import Path
import argparse, shutil
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('task',choices=[f'{i:02d}' for i in range(1,7)]); a=p.parse_args()
base=ROOT/'attempts'/f'task{a.task}'
if base.exists(): shutil.rmtree(base)
print(f'Reset {base}')
