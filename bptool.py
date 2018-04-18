# bptool.py
# Authors: Ronald L. Rivest, Mayuri Sridhar, Zara A Perumal
# April 23, 2018
# python3

import argparse

from copy import deepcopy
import csv
import numpy as np


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
    Given a specific seed, create and return a Numpy RandomState object,
    to make all the audit actions reproducible.
    """

    if seed is not None:
        seed = convert_int_to_32_bit_numpy_array(seed)
    return np.random.RandomState(seed)


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


def generate_nonsample(tally, total_num_votes, seed):
    """
    Given a tally, the total number of votes in an election, and a seed,
    generate the nonsample votes in the election using the Dirichlet multinomial
    distribution.
    """
    
    rs = create_rs(seed)
    return dirichlet_multinomial(tally, total_num_votes, rs)


def compute_winner(sample_tallies, total_num_votes, seed, pretty_print=False):
    """
    Given a list of sample tallies, the number of votes from each county, and
    a random seed, compute the winner in a single simulation. In particular,
    for each county, we use the Dirichlet-Multinomial distribution to generate
    the nonsample tallies. Then, we sum over all the counties to produce our
    final tally and calculate the predicted winner over all the counties in
    the election.
    """
    
    final_tally = None
    for i, sample_tally in enumerate(sample_tallies):
        nonsample = generate_nonsample(sample_tally, total_num_votes[i], seed)
        final_county_tally = [sum(k) for k in zip(sample_tally, nonsample)]
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


def compute_winner_probabilities(sample_tallies, total_num_votes,
                                 seed,
                                 num_trials,
                                 candidate_names,
                                 pretty_print=True):
    """

    Runs num_trials simulations of the Bayesian audit to find the most plausible winner.

    In particular, we run a single iteration of a Bayesian audit (extend each county's
    sample to simulate all the votes in the county and calculate the overall winner
    across counties) num_trials times. Then, we print the candidate that has won
    the most often, along with the number of trials they have won.
    """

    winners = {(k + 1): 0 for k in range(len(sample_tallies[0]))}
    for i in range(num_trials):
        winners[compute_winner(sample_tallies, total_num_votes, seed) + 1] += 1
    winners_list = list(winners.items())
    most_likely_winner = winners_list.index(
        max(winners_list, key=lambda x: x[1]))

    if pretty_print:
        print("With %d trials in total" % num_trials, end=" ")
        print("and candidates: %s" % str(candidate_names))
        print("Simulation results are:")
        sorted_winners_list = sorted(
            winners_list, key=lambda tup: tup[1], reverse=True)
        print("Candidate name \t\t Estimate probability of winning a full recount ")
        for candidate_index, votes in sorted_winners_list:
            candidate_name = str(candidate_names[candidate_index - 1])
            vote_percent = int(votes) / float(num_trials)
            print("%s \t\t\t %.02f  " % (candidate_name, vote_percent))


def preprocess_audit_seed(audit_seed):
    """
    Preprocesses the audit seed to make it of type int, if it isn't None.
    """

    if audit_seed is not None:
        audit_seed = int(audit_seed)
    return audit_seed


def preprocess_single_tally(sample_tally_list):
    """
    Preprocesses a single tally passed in as an argument. In particular,
    strips spaces and converts each comma-separated element of the tally
    into an integer.
    """

    return [sample_tally_list]


def preprocess_csv(path_to_csv):
    """
    Preprocesses a CSV file into the correct format for our
    sample tallies. In particular, we ignore the county name column and
    the name of the candidates. However, we create a sample_tallies list
    and a total_num_votes list, which contain the relevant information
    about each county election.

    Sample_tallies[i] is a list of ints, where sample_tallies[i][j]
    represents the number of votes for candidate j in the sample tally
    for county i. Similarly, total_num_votes[i] represents the total
    number of votes in county i.
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
                    sample_tally.append(int(row[key].strip()))
            sample_tallies.append(sample_tally)
    return sample_tallies, total_num_votes, candidate_names


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bayesian Audit Process For A Single Contest '
                                                 'Across Multiple Counties')

    parser.add_argument("total_num_votes",
                        help="The total number of votes (including the already audited ones) "
                             "which are included in the election.")

    parser.add_argument("--sample_tally",
                        help="If the election only has one county, "
                             "then pass the tally as space separated numbers,"
                             "e.g.  5 30 25", nargs="*", type=int)

    parser.add_argument("--path_to_csv",
                        help="If the election spans multiple counties, "
                             "it might be easier to pass in the sample tallies "
                             "as a csv file. In this case, pass in the full path to "
                             "the csv file as an argument. One of the column names "
                             "of the csv file must be Total Votes and another can be "
                             "County Name. All other columns are assumed to be the names "
                             "or identifiers for candidates.")

    parser.add_argument("--audit_seed",
                        help="For reproducibility, we provide the option to seed the "
                             "randomness in the audit. If the same seed is provided, the audit "
                             "will return the same results.",
                        default=1)

    parser.add_argument("--num_trials",
                        help="Bayesian audits work by simulating the data "
                             "which hasn't been sampled to predict who the winner is. "
                             "This argument specifies how many simulations we should do to "
                             "predict the winner",
                        default=10000)
    args = parser.parse_args()

    if args.path_to_csv:
        sample_tallies, total_num_votes, candidate_names = preprocess_csv(
            args.path_to_csv)
    else:
        sample_tallies = preprocess_single_tally(args.sample_tally)
        total_num_votes = [int(args.total_num_votes)]
        candidate_names = list(range(len(sample_tallies[0])))

    audit_seed = preprocess_audit_seed(args.audit_seed)

    num_trials = int(args.num_trials)

    compute_winner_probabilities(
        sample_tallies,
        total_num_votes,
        audit_seed,
        num_trials,
        candidate_names)
