# 2018-bptool
Standalone tool for estimating Bayesian posterior loss from election tally for ballot-polling audit.

# Usage
bptool.py can be run with python3 in two methods. 

## Single County
If the election only has one county enter tallies as numbers e.g.
```python3 bptool.py 20000 --sample_tally 5 30 25```

## Multiple Counties
If the election spans multiple counties, it might be easier to pass in the sample tallies as a csv file
```python3 bptool.py 20000 --path_to_csv test.csv```

Additional inforomation on usage and optional arguments can be view via:

```python3 bptool.py -h ```