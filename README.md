# FossilScanner

Field specimen capture, magnetic survey, hardware preflight, and
evidence-ranked identification for Android/Termux and desktop Linux.[span_1](start_span)[span_1](end_span)

## Design stance

FossilScanner separates what was observed from what is hypothesized.
Every interpretive statement carries an evidence state. The
identification pipeline prefers broader ranks and `unresolved` over
a species name that the evidence does not support.[span_2](start_span)[span_2](end_span)

## Install

```bash
bash tools/bootstrap.sh
# or, without install:
export PYTHONPATH=$PWD/src
python3 -m fossil_scanner.cli --help

