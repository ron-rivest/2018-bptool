"""
Simple website form for using BPTool online. Can be hosted
by running "python website.py"
"""
import cherrypy
import os.path

import bptool


class BPToolPage:

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


            <h2>Step 1: Select Single-County or Multi-County Audit</h2>

            <form action="Query" method="GET">
            <p>Select whether you are entering data for a single county or for multiple
            counties.</p>

            <select id="county" name="county">
              <option value="single_county">Single County</option>
              <option value="multiple_counties">Multiple Counties</option>
            </select>


            <h2>Step 2: Enter Candidate Names</h2>

            <p> 
            In the box below, 
            enter the names of the candidates as a comma-separated list.
            </p>

            <p>
            Example:
            <tt>Alice, Bob</tt>
            </p>
            
            Candidate names: <input type="text" name="candidate_names" />


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
            </form>'''

    @cherrypy.expose
    def Query(
        self, sample, total, seed,
        county, num_trials, candidate_names):

        if sample is not "" and total is not "":
            try:
                if seed == "":
                    seed = 1
                if num_trials == "":
                    num_trials = 10000

                if county == 'single_county':
                    total_num_votes = [int(total)]
                    sample_tallies = [[int(k.strip()) for k in sample.split(',')]]
                else:
                    total_num_votes = [int(k.strip()) for k in total.split(',')]
                    split_by_county = [k.strip() for k in sample.split(';')]
                    sample_tallies = []
                    for i in range(len(split_by_county)):
                        tmp = [int(k) for k in split_by_county[i].split(',')]
                        sample_tallies.append(tmp)
                    assert(len(total_num_votes) == len(sample_tallies))

                if candidate_names == "":
                    candidate_names = list(range(1, len(sample_tallies[0]) + 1))
                else:
                    candidate_names = [k.strip() for k in candidate_names.split(',')]

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
                return get_html_results(candidate_names, win_probs)
            except:
                return 'Please make sure all inputs are following the correct format and \
                re-enter them <a href="./">here</a>. A common reason for this error is \
                if you fill in samples for multiple counties but fail to click the appropriate \
                option in the first drop-down menu.'
        else:
            return 'Please enter the sample and the total number of votes <a href="./">here</a>.'

def get_html_results(candidate_names, win_probs):
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

server_conf = os.path.join(os.path.dirname(__file__), 'server_conf.conf')

if __name__ == '__main__':
    cherrypy.quickstart(BPToolPage(), config=server_conf)
