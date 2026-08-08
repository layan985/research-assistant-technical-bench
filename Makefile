.PHONY: bootstrap test scoreboard clean-generated
bootstrap:
	python scripts/bootstrap.py

test:
	pytest -q

scoreboard:
	python scripts/build_scoreboard.py

clean-generated:
	rm -rf exams/task02_large_data/raw exams/task04_scraping/archive exams/task05_text_data/raw/generated_*.csv
