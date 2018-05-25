import argparse
import bptool
import copy
import collections

import numpy as np

def generate_ballots(margin, total_num_votes):
	"""
	Generates an unshuffled list of ballots for a 2-candidate
	election given the margin between the winner and the
	runner-up.

	Input params:
	-margin is a float, representing the percentage margin
	between the winner and the runner-up.
	-total_num_votes is an integer, representing the total
	number of votes cast in the election.

	Returns:
	-A list of length total_num_votes, where each element
	in the list is 0 or 1. There will be margin percent more
	0's than 1's in this list.
	"""
	frac_votes_for_winner = 0.5*(1. + margin / 100.)
	frac_votes_for_loser = 1-frac_votes_for_winner

	num_votes_for_winner = int(total_num_votes*frac_votes_for_winner)
	num_votes_for_loser = total_num_votes - num_votes_for_winner

	ballots_list = []
	ballots_list.extend([0]*num_votes_for_winner)
	ballots_list.extend([1]*num_votes_for_loser)

	return ballots_list

def shuffle_list(ballot_list, audit_seed=1):
	"""
	Given a sorted list of ballots, shuffles the list in
	a random, reproducible order, given the seed.

	Input params:
	-ballot_list is a list of integers, where each entry in ballot list
	corresponds to a single vote. For instance, if ballot_list[0] is 1,
	then that represents a vote for Candidate 1.
	-audit_seed is an integer, used to seed the randomness in shuffling
	the list.

	Returns:
	-shuffled version of ballot_list
	"""
	audit_seed = bptool.convert_int_to_32_bit_numpy_array(audit_seed)
	rs = bptool.create_rs(audit_seed)
	rs.shuffle(ballot_list)

	return ballot_list

def estimate_risk_limit(total_num_votes, margin, sample_size, trials_per_sample,
						num_samples, audit_seed=1):
	"""
	Given the total number of votes in the election, the margin, and a desired
	sample size, calculates the estimated Bayesian risk for the sample size.

	Input params:
	-total_num_votes is an integer, representing the total
	number of votes cast in the election.
	-margin is a float, representing the percentage margin
	between the winner and the runner-up.
	-sample_size is an integer, representing the desired sample size, which
	we are estimating the risk limit for.
	-trials_per_sample is an integer, representing the number of trials used
	to estimate the risk limit for a particular sample.
	-num_samples is an integer, representing the number of different samples
	to try, to estimate the risk limit.
	-audit_seed is an integer, used to seed the randomness in shuffling
	the list.

	Returns:
	-Estimated Bayesian risk across several possible samples of size sample_size.
	"""
	sorted_ballot_list = generate_ballots(margin, total_num_votes)
	risk_estimates = []
	for i in range(num_samples):
		current_list = copy.deepcopy(sorted_ballot_list)

		audit_seed += 31415
		shuffled_list = shuffle_list(current_list, audit_seed)
		sample = shuffled_list[:sample_size]
		current_risk_estimate = 0
		
		seed_i = audit_seed
		for _ in range(trials_per_sample):
			sample_tally_dict = collections.Counter(sample)
			sample_tally = [sample_tally_dict[0], sample_tally_dict[1]]
			seed_i += 6723
			nonsample_tally = bptool.generate_nonsample_tally(
    			sample_tally,
    			total_num_votes, seed_i, pseudocount_for_prior=1)

			if (
				sample_tally[0] + nonsample_tally[0] <=
				sample_tally[1] + nonsample_tally[1]
			):
				current_risk_estimate += 1

		current_risk_estimate /= float(trials_per_sample)
		risk_estimates.append(current_risk_estimate)

	return sum(risk_estimates) / len(risk_estimates)


def main():
	parser = argparse.ArgumentParser(description=\
									'Bayesian Risk Estimator for '
									'a single county election.')

	parser.add_argument("total_num_votes",
						help="Enter the total number of votes cast "
							 "in the election.",
						type=int)

	parser.add_argument("margin",
						help="Enter the percentage margin between the "
							 "winner and the runner-up in the election.",
						type=float)

	parser.add_argument("sample_size",
						help="Enter the sample size that we are estimating "
							 "the Bayesian risk for.",
						type=int)

	parser.add_argument("--trials_per_sample",
						help="(OPTIONAL) Enter the number of trials to estimate "
							 "the Bayesian risk for a single sample.",
						type=int,
						default=1000)

	parser.add_argument("--num_samples",
						help="(OPTIONAL) Enter the number of samples to use in "
							 "estimating the Bayesian risk for a given sample size.",
						type=int,
						default=50)

	parser.add_argument("--audit_seed",
                        help="For reproducibility, we provide the option to "
                             "seed the randomness in the audit. If the same "
                             "seed is provided, the audit will return the "
                             "same results.",
                        type=int,
                        default=1)

	args = parser.parse_args()

	risk_limit = estimate_risk_limit(
		args.total_num_votes,
		args.margin,
		args.sample_size,
		args.trials_per_sample,
		args.num_samples)

	print("The estimated Bayesian risk limit for a sample size of {} in an election "
		  "with {} votes, with a margin of {}%, will be {:6.2f}. \nThis was calculated by generating "
		  "{} different samples, of the same size, and running {} 'restore' operations "
		  "on each sample, to estimate its risk limit.".format(
		  	args.sample_size, args.total_num_votes, args.margin, risk_limit,
		  	args.num_samples, args.trials_per_sample))

if __name__ == '__main__':
	main()

