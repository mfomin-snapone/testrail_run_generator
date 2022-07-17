"""
Example on how to use the bulk add test results function add_test_results.  For this one you need the test id's from the
test run, NOT the case id's from the suite.

NOTE: You have to put in valid id's for test_id's and run.  Don't just run it with example values.  Its possible
those values already exist in the system and you may actually update a live run you weren't intending to.
"""

from ..pytestrail import PyTestRail

# this id is located in the upper left of the test run page for the run you want to use.  It starts with an R.
# leave the R off.
test_run_id_to_update = 3045

# To find the test id, open up the test case in the test run and look in the upper left.  It starts with a T.  Leave
# the T off.  Grab the id's for all the tests you want to update
test_ids_to_update = [1396413, 1396410, 1396411]

# the user is what you use to log into test rail with.  The api key is either your password (dont use this) or an
# api key for your user.  set up api keys by going into your user settings > api keys tab > add api key.
testrail_user = 'bzuck@control4.com'
testrail_api_key = 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.'
ptr = PyTestRail(testrail_user, testrail_api_key)

# list we're going to use to store test results.
results = []

# this iterates through the cases and passses them all.  To fail one or set some other status replace
# ptr.test_status.PASSED with ptr.test_status.FAILED.
for test_id in test_ids_to_update:
    result = ptr.result_builder(test_id
                                , ptr.test_status.PASSED    # required. this maps to the integer value testrail understands
                                , comment='Comment for the test.'   # optional.  comment about the test or logs etc.
                                , version='FW version 1.0.260'    # optional. version of whatever it is you're testing
                                , elapsed='15s' # optional. amount of time the test took
                                # , defects='ES-2567, ES-2568' # optional.  defects in jira.  they auto link if they exist
                                # , assignedto_id=162 # optional.  user id you want the case assigned to
                                # , custom_fields_dict=dict_with_custom_fields # optional, see function description for details
                                , by_case=False # this is false because we're updating via test_id, not case_id
                                )
    results.append(result)

print(results)

# now we have a properly formatted list of result dictionaries.  Lets update testrail
response = ptr.add_test_results(test_run_id_to_update, results)
print('testrail response: {0}'.format(response))




