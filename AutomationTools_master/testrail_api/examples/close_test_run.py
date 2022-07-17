"""
Example on how to close a test run once you're done adding results etc.  The test run has to be in an open state
already for this to work.
"""

from ..pytestrail import PyTestRail

# this id is located in the upper left of the test run page for the run you want to use.  It starts with an R.
# leave the R off.
test_run_id = 3059

# the user is what you use to log into test rail with.  The api key is either your password (dont use password though)
# or an api key for your user.  set up api keys by going into your user settings > api keys tab > add api key.
testrail_user = 'bzuck@control4.com'
testrail_api_key = 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.'

ptr = PyTestRail(testrail_user, testrail_api_key)

# lets close the test run:
response = ptr.close_run(test_run_id)
print('testrail response: {0}'.format(response))
