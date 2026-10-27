.PHONY: setup run sql test notebooks all
setup:     ; pip install -r requirements.txt
run:       ; python -m src.run_pipeline
sql:       ; python sql/run_queries.py
test:      ; python -m pytest -q
# Re-executes notebooks IN PLACE (rewrites the committed outputs). Needs requirements-notebooks.txt.
notebooks: ; cd notebooks && for f in *.ipynb; do jupyter nbconvert --to notebook --execute --inplace $$f; done
all: run sql test
