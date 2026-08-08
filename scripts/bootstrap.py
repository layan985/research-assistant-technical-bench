from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
for d in [ROOT/'attempts', ROOT/'scoreboard/results']:
    d.mkdir(parents=True, exist_ok=True)
subprocess.check_call([sys.executable, str(ROOT/'exams/task01_data_wrangle/generate.py')])
subprocess.check_call([sys.executable, str(ROOT/'exams/task03_event_study/generate.py')])
subprocess.check_call([sys.executable, str(ROOT/'exams/task06_bug_hunt/generate.py')])
print('Bootstrap complete. Task 01, 03, and 06 raw inputs generated.')
