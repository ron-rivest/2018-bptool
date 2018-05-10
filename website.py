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
            <h1> Bayesian Ballot Polling Tool </h1>
            <p>This form provides a simple way to computing the winning probabilities
            for various candidates, given audit sample data, using a Bayesian
            model, in a ballot-polling audit of a plurality election.  The
            election may be single-jurisdiction or multi-jurisdiction.  In this
            module we call a jurisdiction a "county" for convenience, although it
            may be a precinct or a state or something else, as long as you can
            sample from its collection of paper ballots.</p>

            <p> The Bayesian model uses a prior pseudocount of "+1" for each candidate.</p>

            <p> More description of Bayesian auditing methods can be found in: </p>
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

            <p> This web form provides exactly the same functionality as the Python tool
            <a href=https://github.com/ron-rivest/2018-bptool>BPTool.py</a>. The Python tool
            requires an environment set up with Python 3 and Numpy.</p>

            <form action="Query" method="GET">
            <p>Please specify whether you are entering data for a single county or multiple
            counties.</p>
            <select id="county" name="county">
              <option value="single_county">Single County</option>
              <option value="multiple_counties">Multiple Counties</option>
            </select>

            <p> What are the names of the candidates? Please enter as a comma-separated list.</p>
            <input type="text" name="candidate_names" />
            <p>What is the sample tally? Please enter as a comma-separated list of numbers for a
            single county, for example: 1, 3. </p>

            <p>If you would like to enter the tallies for multiple counties, separate
            the tallies between counties with a semicolon. For instance, a tally of the form:
            1, 3; 2, 4 implies there is 1 vote for candidate A in county 1, 3 votes for candidate
            B in county 1, 2 votes for candidate A in county 2 and 4 votes for candidate B in county 2.</p>

            <p>Note that this must be in the same order as the name of the candidates specified above. For
            instance, if your input for the names was Alice, Bob and the tally is 2, 3, this is interpreted
            as two votes for Alice and 3 for Bob.</p>

            <input type="text" name="sample" />
            <p>What is the total number of votes in the county? Please enter a number for a single county, like
            50.</p>
            <p> For multiple counties, enter a comma-separated list for multiple counties. For instance,
            50, 60 implies there are 50 votes total in County 1 and 60 in County 2.</p>

            <p>Like before, this must
            be in the same order as the sample tallies. That is, if the sample is 1, 2; 3, 4 and the
            total number of votes are 50, 60, this is interpreted as 1 vote for A from county 1,
            2 votes for B from county 1, 50 votes total in county 1 etc. </p>
            <input type="text" name="total" />
            <p>For reproducibility, we provide the option to seed the randomness in the audit.
            If the same seed is provided, the audit will return the 
            same results. This is an optional parameter, which defaults to 1. If you'd like to specify
            a different seed, pass in an integer argument here.</p>
            <input type="text" name="seed" />
            <p>Bayesian audits work by simulating the data which hasn't been sampled to
            estimate the chance that each candidate would win a full hand recount.
            This argument specifies how many trials are done to compute these estimates.
            This is an optional parameter, defaulting to 10000. If you'd like to change this,
            please enter an integer argument here.</p>
            <input type="text" name="num_trials" />
            <input type="submit" />
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
                  "Estimated probability of winning a full recount"))
    results_str += '</tr>'

    for candidate_index, prob in sorted_win_probs:
        candidate_name = str(candidate_names[candidate_index - 1])
        results_str += '<tr>'
        results_str += ('<td style="text-align:center">{:<24s}</td>').format(candidate_name)
        results_str += ('<td style="text-align:center">{:6.2f} %</td>').format(100*prob)
        results_str += '</tr>'
    results_str += '</table>'
    results_str += '<p> Click <a href="./">here</a> to go back to the home page and try again.</p>'
    return results_str

server_conf = os.path.join(os.path.dirname(__file__), 'server_conf.conf')

if __name__ == '__main__':
    cherrypy.quickstart(BPToolPage(), config=server_conf)