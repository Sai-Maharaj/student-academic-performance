# Student Academic Performance Analysis and Data Visualization System

An interactive Streamlit dashboard for exploring academic marks, attendance and semester performance.

## Features

- Validated CSV import (UTF-8, up to 5 MB and 20,000 rows).
- Department, semester, subject, student search and academic-support filters.
- Six interactive Plotly charts, student summaries and detailed records.
- CSV, JSON and standalone interactive HTML exports.
- Synthetic sample: 120 fictional students and 1,800 subject records.

## Run locally

Use Python 3.12. Install dependencies and start the dashboard:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

Connect this repository to Streamlit Community Cloud. Select branch `main`, entrypoint `app.py`, and Python 3.12 in advanced settings.

## Data and methodology

The bundled records are entirely synthetic. Download the CSV template from the app to see the required columns. Total marks equal Internal (0-25) + External (0-60) + Assignment (0-15). A subject passes at 40/100. A support flag means marks below 40 or attendance below 75%. These are illustrative thresholds, not verified college regulations or automated academic decisions. Correlations are descriptive and do not establish causation.

Uploaded files are sent to the hosting server and processed in session memory. The application does not write uploads to a file or database. Use synthetic or anonymized records for this public demonstration.
