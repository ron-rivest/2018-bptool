# bptool.py
# Authors: Ronald L. Rivest, Mayuri Sridhar, Zara A Perumal
# April 19, 2018
# python3

"""
This module provides routines for computing the winning probabilities
for various candidates, given audit sample data, using a Bayesian
model, in a ballot-polling audit of a plurality election.  The
election may be single-jurisdiction or multi-jurisdiction.  In this
module we call a jurisdiction a "county" for convenience, although it
may be a precinct or a state or something else, as long as you can
sample its collection of paper ballots.

The Bayesian model uses a prior pseudocount of "+1" for each candidate.

If this module is imported, rather than used stand-alone, then the procedure
    compute_win_probs 
can compute the desired probability of each candidate winning a full recount,
given sample tallies for each county.

For command-line usage, there are really two modes:
(1) For single-county usage, give a command like:
        python bptool.py 10000 60 50 30
    where
        10000 is the total number of votes cast in the county
        60 50 30  are the votes seen for each candidate in the auditing so far

(2) For multiple-county usage, give a command like
        python bptool.py --path_to_csv test.csv
    where test.csv is a file like:
        county name, total votes, Alice, Bob
        1, 1000, 30, 15
        2, 2000, 40, 50
    with one header line, then one line per county.  The field names
    "county name" and "total votes" are required; the candidate names are
    the candidate names for the contest being audited.

There are optional parameters as well, to see the documentation of them, do
    python bptool.py --h
"""


import argparse

from copy import deepcopy
import csv
import numpy as np
import sys

##############################################################################
## Random number generation
##############################################################################

# This function is taken from audit-lab directly.
def convert_int_to_32_bit_numpy_array(v):
    """
    Convert value v, which should be an arbitrarily large python integer
    (or convertible to one) to a numpy array of 32-bit values,
    since this format is needed to initialize a numpy.random.RandomState
    object.  More precisely, the result is a numpy array of type int64,
    but each value is between 0 and 2**32-1, inclusive.

    Example: input 2**64 + 5 yields np.array([5, 0, 1], dtype=int)
    """

    v = int(v)
    if v < 0:
        raise ValueError(("convert_int_to_32_bit_numpy_array: "
                          "{} is not a nonnegative integer, "
                          "or convertible to one.").format(v))
    v_parts = []
    radix = 2 ** 32
    while v > 0:
        v_parts.append(v % radix)
        v = v // radix
    # note: v_parts will be empty list if v==0, that is OK
    return np.array(v_parts, dtype=int)


def create_rs(seed):
    """
    Create and return a Numpy RandomState object for a given seed. 
    The input seed should be a python integer, arbitrarily large.
    The purpose of this routine is to make all the audit actions reproducible.
    """

    if seed is not None:
        seed = convert_int_to_32_bit_numpy_array(seed)
    return np.random.RandomState(seed)


##############################################################################
## Main computational routines
##############################################################################

def dirichlet_multinomial(sample_tally, total_num_votes, rs):
    """
    Return a sample according to the Dirichlet multinomial distribution,
    given a sample tally, the number of votes in the election,
    and a random state. There is an additional pseudocount of
    one vote per candidate in this simulation.
    """

    sample_size = sum(sample_tally)
    if sample_size > total_num_votes:
        raise ValueError("total_num_votes {} less than sample_size {}."
                         .format(total_num_votes, sample_size))

    nonsample_size = total_num_votes - sample_size

    pseudocount_for_prior = 1
    sample_with_prior = deepcopy(sample_tally)
    sample_with_prior = [k + pseudocount_for_prior
                         for k in sample_with_prior]

    gamma_sample = [rs.gamma(k) for k in sample_with_prior]
    gamma_sample_sum = float(sum(gamma_sample))
    gamma_sample = [k / gamma_sample_sum for k in gamma_sample]

    multinomial_sample = rs.multinomial(nonsample_size, gamma_sample)

    return multinomial_sample


def generate_nonsample_tally(tally, total_num_votes, seed):
    """
    Given a tally, the total number of votes in an election, and a seed,
    generate the nonsample tally in the election using the Dirichlet multinomial
    distribution.
    """

    rs = create_rs(seed)
    nonsample_tally = dirichlet_multinomial(tally, total_num_votes, rs)
    return nonsample_tally


def compute_winner(sample_tallies, total_num_votes, seed, pretty_print=False):
    """
    Given a list of sample tallies (one sample tally per county)
    a list giving the total number of votes cast in each county, 
    and a random seed (an integer)
    compute the winner in a single simulation. 
    For each county, we use the Dirichlet-Multinomial distribution to generate
    a nonsample tally. Then, we sum over all the counties to produce our
    final tally and calculate the predicted winner over all the counties in
    the election.
    """

    final_tally = None
    for i, sample_tally in enumerate(sample_tallies):   # loop over counties
        nonsample_tally = generate_nonsample_tally(
            sample_tally, total_num_votes[i], seed)
        final_county_tally = [sum(k)
                              for k in zip(sample_tally, nonsample_tally)]
        if final_tally is None:
            final_tally = final_county_tally
        else:
            final_tally = [sum(k)
                           for k in zip(final_tally, final_county_tally)]
    winner = final_tally.index(max(final_tally))
    if pretty_print:
        print('Candidate {} is the winner with {} votes. '
              'The final vote tally for all the candidates was {}'.format(
                  winner, final_tally[winner], final_tally))
    return winner


def compute_win_probs(sample_tallies,
                      total_num_votes,
                      seed,
                      num_trials,
                      candidate_names):
    """

    Runs num_trials simulations of the Bayesian audit to estimate the probability that
    each candidate would win a full recount.

    In particular, we run a single iteration of a Bayesian audit (extend each county's
    sample to simulate all the votes in the county and calculate the overall winner
    across counties) num_trials times.  

    Return a list of pairs (i, p) where p is the fraction of the time candidate i has won.
    """

    num_candidates = len(candidate_names)
    win_count = [0]*(1+num_candidates)
    for i in range(num_trials):
        # We want a different seed per trial.
        # Adding i to seed caused correlations, as numpy apparently
        # adds one per trial, so we multiply i by 314...
        seed_i = seed + i*314159265                 
        winner = compute_winner(sample_tallies,
                               total_num_votes,
                               seed_i)
        win_count[winner+1] += 1
    win_probs = [(i, win_count[i]/float(num_trials))
                 for i in range(1, len(win_count))]
    return win_probs


##############################################################################
## Routines for command-line interface and file (csv) input
##############################################################################

def print_results(candidate_names, win_probs):
    """
    Given list of candidate_names and win_probs 
    (a list of (winner index, winning prob) pairs, print summary
    """

    print("BPTOOL (version 0.8)")

    want_sorted_results = True
    if want_sorted_results:
        sorted_win_probs = sorted(
            win_probs, key=lambda tup: tup[1], reverse=True)
    else:
        sorted_win_probs = win_probs

    print("{:<24s} \t {:<s}"
          .format("Candidate name",
                  "Estimated probability of winning a full recount"))

    for candidate_index, prob in sorted_win_probs:
        candidate_name = str(candidate_names[candidate_index - 1])
        print(" {:<24s} \t  {:6.2f} %  "
              .format(candidate_name, 100*prob))


def preprocess_csv(path_to_csv):
    """
    Preprocess a CSV file into the correct format for our
    sample tallies. In particular, we ignore the county name column.
    However, we create a sample_tallies list
    and a total_num_votes list, which contain the relevant information
    about each county election.  We also return a list of candidate names.

    Sample_tallies[i] is a list of ints, where sample_tallies[i][j]
    represents the number of votes for candidate j in the sample tally
    for county i. Similarly, total_num_votes[i] represents the total
    number of votes cast in county i.
    """

    with open(path_to_csv) as csvfile:
        sample_tallies = []
        total_num_votes = []
        reader = csv.DictReader(csvfile)
        candidate_names = [col for col in reader.fieldnames
                           if col.strip().lower() not in
                           ["county name", "total votes"]]
        for row in reader:
            sample_tally = []
            for key in row:
                if key.strip().lower() == "county name":
                    continue
                if key.strip().lower() == "total votes":
                    total_num_votes.append(int(row[key]))
                else:
                    count = int(row[key].strip())
                    assert 0 <= count 
                    sample_tally.append(count)
            sample_tallies.append(sample_tally)

    for i, sample_tally in enumerate(sample_tallies):
        assert 0 <= sum(sample_tally) <= total_num_votes[i]

    return sample_tallies, total_num_votes, candidate_names


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Bayesian Audit Process For A Single Contest '
                                                 'Across One or More Counties')

    parser.add_argument("total_num_votes",
                        nargs="?",
                        help="(Optional: for single-county audits:) The total number of votes"
                             "(including the already audited ones) "
                             "that were cast in the election.")

    parser.add_argument("single_county_tally",
                        help="(Optional: for single-county audits:) the tally given as space separated numbers,"
                             "e.g.  5 30 25",
                        nargs="*",
                        default=[],
                        type=int)

    parser.add_argument("--path_to_csv",
                        help="If the election spans multiple counties, "
                             "the sample tallies should be given in a csv file." 
                             "Give here the csv file pathname as an argument. "
                             "In the header row, one of the column names "
                             "of the csv file must be Total Votes and another can be "
                             "County Name. Other columns are the names "
                             "or identifiers for candidates.")

    parser.add_argument("--audit_seed",
                        help="For reproducibility, we provide the option to seed the "
                             "randomness in the audit. If the same seed is provided, the audit "
                             "will return the same results.",
                        type=int,
                        default=1)

    parser.add_argument("--num_trials",
                        help="Bayesian audits work by simulating the data "
                             "which hasn't been sampled to estimate the chance that "
                             "each candidate would win a full hand recount. "
                             "This argument specifies how many trials are done to "
                             "compute these estimates.",
                        type=int,
                        default=10000)

    args = parser.parse_args()
    if args.path_to_csv==None and args.total_num_votes==None:
        parser.print_help()
        sys.exit()

    if args.path_to_csv:
        # if sample tallies are in CSV file read that
        sample_tallies, total_num_votes, candidate_names = \
            preprocess_csv(args.path_to_csv)
    else:
        # otherwise extract desired data from command line
        total_num_votes = [int(args.total_num_votes)]
        sample_tallies = [args.single_county_tally]
        candidate_names = list(range(1, len(sample_tallies[0]) + 1))

    win_probs = compute_win_probs(
                    sample_tallies,
                    total_num_votes,
                    args.audit_seed,
                    args.num_trials,
                    candidate_names)
    print_results(candidate_names, win_probs)
