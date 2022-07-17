"""
Example on how to use the bulk add test results function add_test_results for case_id's.  This one is nice since
the case id for a test is always the same regardless of the run its in.  So you dont have to query the test run
first to find out what the test_id's are for the tests you want to update.

NOTE: You have to put in valid id's for case_id's and run.  Don't just run it with example values.  Its possible
those values already exist in the system and you may actually update a live run you weren't intending to.
"""

from ..pytestrail import PyTestRail

# this id is located in the upper left of the test run page for the run you want to use.  It starts with an R.
# leave the R off.
test_run_id_to_update = 3059

# To find the case id, open up the test case in the test suite and look in the upper left.  It starts with a C.  Leave
# the C off.  Grab the id's for all the tests you want to update
case_ids_to_update = [1034070, 1034071, 1034072]

# the user is what you use to log into test rail with.  The api key is either your password (dont use password though)
# or an api key for your user.  set up api keys by going into your user settings > api keys tab > add api key.
testrail_user = 'bzuck@control4.com'
testrail_api_key = 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.'

ptr = PyTestRail(testrail_user, testrail_api_key)

# list we're going to use to store test result dictionaries.
results = []

# this iterates through the cases and passses them all.  To fail one or set some other status replace
# ptr.test_status.PASSED with ptr.test_status.FAILED.  You can also forgo the loop and update each case
# individually.
for case_id in case_ids_to_update:
    result = ptr.result_builder(case_id
                                , ptr.test_status.PASSED    # required. this maps to the integer status value testrail understands
                                , comment='updated by case.  Comment for the test.'   # optional.  comment about the test or logs etc.
                                , version='FW version 1.0.261'    # optional. version of whatever it is you're testing
                                , elapsed='15s' # optional. amount of time the test took
                                # , defects=['ES-2567', 'ES-2568'] # optional.  defects in jira.  they auto link if they exist
                                # , assignedto_id=162 # optional.  user id you want the case assigned to
                                # , custom_fields_dict=dict_with_custom_fields # optional, see function description for details
                                )
    results.append(result)

print(results)

# now we have a properly formatted list of result dictionaries.  Lets update testrail
response = ptr.add_test_results(test_run_id_to_update, results)
print('testrail response: {0}'.format(response))





