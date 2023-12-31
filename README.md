# White Elephant

This repo contains the simulation code (and some of the analysis code) from [White Elephant is surprisingly effective](https://bobbiec.github.io/white-elephant.html).
Hope it helps you in your own exploration!

Please let me know if you find any issues, especially if they would affect the analysis.

## Prerequisites

- Python 3.8+

## Quickstart

```shell
# Set up virtual env and dependencies
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# Generate results-*.csv
python whiteelephant.py

# Generate rank-*.html Plotly pages
python analysis.py
```

## Other tips

- `whiteelephant.py` has a debug print function, `dprint` - change the `if False` to `if True` to see debugging output
- In `analysis.py`, replace the `fig.write_html()` with `fig.show()` when iterating (and it's faster in a notebook)
