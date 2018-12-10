"""
Simple website form for using BPTool online. Can be hosted
by running "python website.py"
"""
import cherrypy
import os.path

import bptool


class BPToolPage:

    def __init__(self):
        self.samples_tool = SamplesToolPage()

    @cherrypy.expose
    def index(self):
        # Ask for the parameters required for the Bayesian Audit.
        # Style parameters from 
        # https://www.w3schools.com/css/tryit.asp?filename=trycss_forms
        return '''
            <style>
            input[type=text], select {
                width: 50%;
                padding: 12px 20px;
                margin: 8px 0;
                display: inline-block;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
            }
            input[type=submit] {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 15px 20px;
                margin: 8px 0;
                border-radius: 4px;
            }
            </style>
            <h1> Bayesian Ballot-Polling Tool </h1>
            <p>
            This page enables you to compute
            the probability that each candidate would win in a full manual recount
            given audit sample data for a single contest.
            The computation uses a Bayesian
            model for a ballot-polling audit.
            The contest is assumed to be a plurality contest (most votes win).
            The
            election may be single-jurisdiction or multi-jurisdiction.  Here
            we call a jurisdiction a "county" for convenience, although it
            may be a precinct or a state or something else, as long as you can
            sample from its collection of paper ballots.</p>

            <h2> References and Code</h2>
            <p> Descriptions of Bayesian auditing methods can be found in: </p>
            <ul>
            <li><a href="http://people.csail.mit.edu/rivest/pubs.html#RS12z">
            A Bayesian Method for Auditing Elections</a>
            by Ronald L. Rivest and Emily Shen
            EVN/WOTE'12 Proceedings
            </li>

            <li><a href="http://people.csail.mit.edu/rivest/pubs.html#Riv18a">
            Bayesian Tabulation Audits: Explained and Extended</a>
            by Ronald L. Rivest 
            2018
            </li> 

            <li><a href="http://people.csail.mit.edu/rivest/pubs.html#Riv18b">
            Bayesian Election Audits in One Page</a>
            by Ronald L. Rivest
            2018
            </li>

            </ul>

            <h2>Implementation Note</h2>
            <p> The code for this tool is available on github at 
            <a href="https://github.com/ron-rivest/2018-bptool">www.github.com/ron-rivest/2018-bptool</a>.
            This web form provides exactly the same functionality as the stand-alone 
            Python tool
            <a href=https://github.com/ron-rivest/2018-bptool>www.github.com/ron-rivest/2018-bptool/BPTool.py</a>. 
            The Python tool
            requires an environment set up with Python 3 and Numpy.
            This web form was implemented using 
            <a href="https://github.com/cherrypy/cherrypy">
            CherryPy
            </a>.

            </p>
            <h2> Escalating the Audit </h2>
            <p> After running a single round of the audit, if the Bayesian risk limit
            is not satisfied, we can increase the sample size of the audit across counties.
            An easy way to do this is by using the <a href="./samples_tool">Sample Escalation Tool</a>.
            </p>


            <form action="Query" method="GET">

            <h2>Step 1: Enter Candidate Names</h2>

            <p> 
            In the box below, 
            enter the names of the candidates as a comma-separated list.
            </p>

            <p>
            Example:
            <tt>Alice, Bob</tt>
            </p>
            
            Candidate names: <input type="text" name="candidate_names" />

            <h2>Step 2: Enter Number of Counties</h2>

            <p>In the box below, enter the number of counties being audited
            as a comma-separated list.</p>

            <p>
            Example:
            <tt>4</tt>
            </p>

            Number of Counties: <input type="text" name="num_counties" />

            <h2>Step 3: Enter number of votes cast per county</h2>
            <p>
            In the box below,
            enter the total number of votes cast in each county.
            For multiple counties, separate entries with commas.
            </p>

            <p>
            Single-county example:
            <tt>101277</tt>
            </p>
            <p>
            Multi-county example:
            <tt>101277, 231586, 50411</tt>
            </p>

            Votes cast per county: <input type="text" name="total" />


            <h2>Step 4: Enter tally for audit sample</h2>

            <p>In the box below, specify the tally for the sample drawn so far
            in the audit.
            </p>

            <p>
            For a single county, just give
            a comma-separated list of numbers, one tally count per candidate,
            in the same order as the candidate names
            given above. 
            </p>


            <p>For multiple counties, separate
            the tallies for different counties with a semicolon. 
            The county segments must be in the same order as used
            earlier for the county sizes.

            <p>
            Single-county example:
            <tt>47, 62</tt> </p>
            In this single-county two-candidate example, the audit has
            seen 47 votes for Alice and 62 votes for Bob.
            </p>
            <p>
            Multi-county example:
            <tt> 47, 62; 101, 84; 17, 99</tt>
            </p>
            <p>
            In this multi-county (three-county two-candidate) example, 
            the sample in county 2 had 101 votes for Alice.
            </p>

            Sample tallies by county: <input type="text" name="sample" />


            <h2>(Optional) Specify random number seed</h2>
            <p>
            The computation uses a random number seed, which defaults to 1.
            You may if you wish enter a different seed here.
            (Using the same seed with the same data always returns the same results.)
            This is an optional parameter; there should be no reason to change it.
            </p>

            Seed: <input type="text" name="seed" />

            <h2>(Optional) Specify number of trials</h2>
            <p>Bayesian audits work by simulating the data which hasn't been sampled to
            estimate the chance that each candidate would win a full hand recount.
            You may specify in the box below the number of 
            trials used to compute these estimates.
            This is an optional parameter, defaulting to 10000.  Making it smaller
            will decrease accuracy and improve running time; making it larger will
            improve accuracy and increase running time. 
            </p>
         
            Number of trials:<input type="text" name="num_trials" />
        
            <h2>Compute results</h2>
            Click on the "Submit" button below to compute the desired answers,
            which will be shown on a separate page.
            <input type="submit" />

            Note: The Bayesian prior is represented by a pseudocount of one vote for
            each choice.  This may become an optional input parameter later.
            </form>
            '''

    @cherrypy.expose
    def Query(
        self, sample, total, seed,
        num_counties, num_trials, candidate_names):

        if sample is not "" and total is not "":
            try:
                if seed == "":
                    seed = 1
                if num_trials == "":
                    num_trials = 10000

                if candidate_names == "":
                    candidate_names = list(range(1, len(sample_tallies[0]) + 1))
                else:
                    candidate_names = [k.strip() for k in candidate_names.split(',')]

                if int(num_counties) == 1:
                    try:
                        total = int(total)
                    except Exception as e:
                        raise AssertionError("For a single county contest, the \
                            total number of votes should be submitted as an integer.")
                    assert(';' not in sample), "For a single county contest, the \
                        number of samples should be specified as a single comma-separated \
                        list, with no semicolons."
                    total_num_votes = [int(total)]
                    sample_tallies = [[int(k.strip()) for k in sample.split(',')]]
                    assert(len(sample_tallies[0]) == len(candidate_names)), "The length \
                        of the sample tallies list, for a single county, should equal \
                        the number of candidates in the race."
                else:
                    total_num_votes = [int(k.strip()) for k in total.split(',')]
                    split_by_county = [k.strip() for k in sample.split(';')]
                    sample_tallies = []
                    for i in range(len(split_by_county)):
                        tmp = [int(k) for k in split_by_county[i].split(',')]
                        assert(len(tmp) == len(candidate_names)), "The list \
                        of the sample tallies, in any given county, should be a \
                        comma-separated list with length equal to the number of \
                        candidates in the race. This isn't true for County {}".format(i+1)
                        sample_tallies.append(tmp)
                    assert(len(total_num_votes) == len(sample_tallies)), "The number of \
                        counties we specify the total number of votes for should be equal \
                        to the number of counties we specify the sample tallies for."
                    assert(len(sample_tallies) == int(num_counties)), "The number of counties \
                        we specify the sample tallies for should be equal to the total number \
                        of counties we are auditing."

                win_probs = bptool.compute_win_probs(\
                        sample_tallies=sample_tallies,
                        total_num_votes=total_num_votes,
                        seed=int(seed),
                        num_trials=int(num_trials),
                        candidate_names=candidate_names,
                        # default pseudocount_for_prior, prior of 1 vote per candidate.
                        pseudocount_for_prior=1,
                        # this is the default vote_for_n value, where each person votes for 1 candidate
                        vote_for_n=1
                    )
                return self.get_html_results(candidate_names, win_probs)
            except Exception as e:
                return 'Please make sure all inputs are following the correct format and \
                re-enter them <a href="./">here</a>.<br> \
                The submitted form caused the following error message: <br> {}'.format(e)
        else:
            return 'Please enter the sample and the total number of votes <a href="./">here</a>.'

    def get_html_results(self, candidate_names, win_probs):
        """
        Given list of candidate_names and win_probs pairs, print summary
        of the Bayesian audit simulations.

        Input Parameters:

        -candidate_names is an ordered list of strings, containing the name of
        every candidate in the contest we are auditing.

        -win_probs is a list of pairs (i, p) where p is the fractional
        representation of the number of trials that candidate i has won
        out of the num_trials simulations.

        Returns:

        -String of HTML formatted results, which make a table on the online
        BPTool.
        """

        results_str = (
            '<style> \
            table, th, td { \
                     border: 1px solid black; \
            }\
            </style>\
            <h1> BPTOOL (Bayesian ballot-polling tool version 0.8) </h1>')

        want_sorted_results = True
        if want_sorted_results:
            sorted_win_probs = sorted(
                win_probs, key=lambda tup: tup[1], reverse=True)
        else:
            sorted_win_probs = win_probs

        results_str += '<table style="width:100%">'
        results_str += '<tr>'
        results_str += ("<th>{:<24s}</th> <th>{:<s}</th>"
              .format("Candidate name",
                      "Estimated probability of winning a full manual recount"))
        results_str += '</tr>'

        for candidate_index, prob in sorted_win_probs:
            candidate_name = str(candidate_names[candidate_index - 1])
            results_str += '<tr>'
            results_str += ('<td style="text-align:center">{:<24s}</td>').format(candidate_name)
            results_str += ('<td style="text-align:center">{:6.2f} %</td>').format(100*prob)
            results_str += '</tr>'
        results_str += '</table>'
        results_str += '<p> Click <a href="./">here</a> to go back to the main page.</p>'
        return results_str

class SamplesToolPage:

    @cherrypy.expose
    def index(self):
        # Ask for the parameters to escalate an audit.
        # Style parameters from 
        # https://www.w3schools.com/css/tryit.asp?filename=trycss_forms
        return '''
            <style>
            input[type=text], select {
                width: 50%;
                padding: 12px 20px;
                margin: 8px 0;
                display: inline-block;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
            }
            input[type=submit] {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 15px 20px;
                margin: 8px 0;
                border-radius: 4px;
            }
            </style>
            <h1> Sample Escalation Tool </h1>
            <p>
            This page enables you to escalate the number of samples from each
            county during an audit. That is, we assume that there is some set of
            samples <i>s</i>. In the beginning of an audit, this set might be empty.
            If the samples don't satisfy the relevant risk limit,
            this tool provides a way to choose how many additional samples should be
            chosen from each county.</p>

            <p>In particular, we assume that we have the required number of additional
            samples, <i>k</i> to get in the next round. We also know the number of total votes
            in each county of our audit. In the single-county case, we would simply
            poll <i>k</i> additional ballots from the county. This tool is for use
            in the multiple county case.</p>

            <p>For instance, let's assume we have 4 votes
            left in county 1 and 2 votes left in county 2. We can represent this
            as the list:
            </p>

            <p><tt>[1, 1, 1, 1, 2, 2]</tt></p>

            <p>Then, we shuffle this list, randomly, using the audit seed set below.
            For the default audit seed of 1, this gives us the shuffled list:
            </p>
            <p><tt>[1, 2, 2, 1, 1, 1]</tt></p>
            <p>This implies that if we wanted to get one 
            additional sample, we would get it from County 1. If we wanted two additional
            samples, we would get 1 sample from County 1 and 1 sample from County 2,
            and so on. </p>

            <form action="GetSampleSize" method="GET">

            <h2>Step 1: Enter County Names</h2>

            <p>In the box below, enter the names of each county that is being audited
            as a comma-separated list.
            </p>
            <p>
            Example:
            <tt> County A, County B </tt>
            </p>

            County Names: <input type="text" name="county_names" />

            <h2>Step 2: Enter Total Votes Per County</h2>

            <p>In the box below, enter the total number of ballots in each county,
            including those already sampled, as a comma-separated list.</p>

            <p>
            Example:
            <tt>1500, 2000</tt>
            </p>

            Number of Ballots per County: <input type="text" name="votes_per_county" />


            <h2>Step 3: Enter Current Sample Sizes</h2>

            <p> 
            In the box below, 
            enter the sample size in each county as a comma-separated list. If no
            samples have been collected yet, this box can be left blank.
            </p>

            <p>
            Example:
            <tt>50, 75</tt>
            </p>
            
            Current Sample Sizes: <input type="text" name="current_samples" />

            <h2> Step 4: Enter Additional Required Sample Size</h2>

            <p> In the box below, enter the total number of additional ballots to sample,
            over all the counties, for the next stage in the audit. This should be
            an integer value. </p>

            <p>
            Example:
            <tt>50</tt>
            </p>

            Additional Sample Size: <input type="text" name="additional_sample_size" />

            <h2>(Optional) Specify random number seed</h2>
            <p>
            The computation uses a random number seed, which defaults to 1.
            You may if you wish enter a different seed here.
            (Using the same seed with the same data always returns the same results.)
            This is an optional parameter; there should be no reason to change it.
            </p>

            Seed: <input type="text" name="seed" />

        
            <h2>Compute results</h2>
            Click on the "Submit" button below to compute the desired answers,
            which will be shown on a separate page.
            <input type="submit" />

            </form>
            '''

    @cherrypy.expose
    def GetSampleSize(
        self, county_names,
        current_samples, votes_per_county,
        additional_sample_size, seed
    ):
        '''
        Given the required additional sample size, the current samples in each county
        and the total votes in each county, randomly allocate how many additional
        samples to poll from each county.

        In particular, if there are n_i ballots left over in county i, make a list containing
        n_i instances of the number i. Then, shuffle the list, and 
        given an additional sample size of k, choose the first k elements. In this prefix,
        if there are s_i instances of the number i, then poll an additional s_i ballots
        from county i.
        '''
        try:
            if votes_per_county == "":
                raise AssertionError("The total number of votes in each county must \
                    be specified.")
            
            votes_per_county = [int(k.strip()) for k in votes_per_county.split(',')]

            if current_samples == "":
                current_samples = [0]*len(votes_per_county)
            else:
                current_samples = [int(k.strip()) for k in current_samples.split(',')]

            if additional_sample_size == "":
                raise AssertionError("The required additional sample size for the next \
                    stage in the ballot must be specified as an integer value.")

            additional_sample_size = int(additional_sample_size)

            assert(len(current_samples) == len(votes_per_county)), "The length of the \
                input list for current sample sizes should equal the length of the input list \
                for the total votes per county. In particular, these values should both \
                equal the number of counties in the audit."

            county_names = [k.strip() for k in county_names.split(',')]

            assert(len(county_names) == len(votes_per_county)), "The length of the input list \
                for the total number of votes in each county should equal the number of counties \
                specified in Step 1."

            votes_tally = []
            for county in range(len(current_samples)):
                leftover_votes = votes_per_county[county] - current_samples[county]
                assert(leftover_votes >= 0), "The number of total votes in a county cannot \
                    exceed the number of votes in the sample. This is violated for county {}".format(
                        county + 1)
                votes_tally.extend([county+1]*leftover_votes)

            if seed == "":
                seed = 1
            else:
                seed = int(seed)

            rs = bptool.create_rs(seed)
            rs.shuffle(votes_tally)

            additional_samples = votes_tally[:additional_sample_size]

            return self.get_html_results(additional_samples, county_names)

        except Exception as e:
            return 'Please make sure all inputs are following the correct format and \
            re-enter them <a href="./">here</a>.<br> \
            The submitted form caused the following error message: <br> {}'.format(e)

    def get_html_results(self, additional_samples, county_names):
        '''
        Given the county names and the appropriately sized prefix of how many
        additional samples to poll from each county, print out the number of
        ballots to poll from each county as an HTML table.

        Input Parameters:

        -additional_samples is a list of integers, where each integer
        in the list ranges from 1 to the total number of counties.
        -county_names is a list of length total number of counties, where
        each element is a string representing the name of a county.

        Returns:

        -String rendering an HTML table representing how many additional
        ballots need to be polled from each county.
        '''
        additional_per_county_tally = {}
        for county in additional_samples:
            additional_per_county_tally[county] = additional_per_county_tally.get(
                county, 0) + 1

        county_index_to_name_map = dict(enumerate(county_names))

        results_str = (
            '<style> \
            table, th, td { \
                     border: 1px solid black; \
            }\
            </style>\
            <h1> Sample Escalation Tool </h1>')


        results_str += '<table style="width:100%">'
        results_str += '<tr>'
        results_str += ("<th>{:<24s}</th> <th>{:<s}</th>"
              .format("County Name",
                      "Number of Additional Ballots to Sample"))
        results_str += '</tr>'

        for county in range(len(county_names)):
            results_str += '<tr>'
            results_str += ('<td style="text-align:center">{}</td>').format(
                county_index_to_name_map[county])
            results_str += ('<td style="text-align:center">{}</td>').format(
                additional_per_county_tally[county+1])
            results_str += '</tr>'
        results_str += '</table>'
        results_str += '<p> Click <a href="./">here</a> to go back to the main page.</p>'
        return results_str


server_conf = os.path.join(os.path.dirname(__file__), 'server_conf.conf')

if __name__ == '__main__':
    cherrypy.quickstart(BPToolPage(), config=server_conf)
