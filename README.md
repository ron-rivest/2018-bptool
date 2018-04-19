# 2018-bptool
Standalone tool for estimating Bayesian posterior loss from election tally for ballot-polling audit.

# Usage
bptool.py can be run with python3 in two ways: one for single-county ballot-polling audits, and one for
multi-county ballot-poling audits.

## Single County
If the election only has one county enter tallies as numbers e.g.

```python3 bptool.py 20000 40 60 10```

where the first number is the total number of votes cast, and the following numbers are the number of
votes seen for each candidate in the auditing done so far.

## Multiple Counties
If the election spans multiple counties, it might be easier to pass in the sample tallies as a csv file

```python3 bptool.py --path_to_csv test.csv```

Additional inforomation on usage and optional arguments can be view via:

```python3 bptool.py -h ```

## Output
The output for a single-county ballot-polling audit might look like (for the above
command ``python bptool.py 200000 40 60 10``):
```BPTOOL (version 0.8)
```Candidate name           	 Estimated probability of winning a full recount
``` 2                        	   97.86 %  
``` 1                        	    2.14 %  
``` 3                        	    0.00 %  

## Importing bptool.py
The module ``bptool.py`` may also be imported into other python code,.  See the
code for guidance.
