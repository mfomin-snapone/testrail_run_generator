"""
Example of how to add a test run based off of an existing test suite and import all test cases from the suite
into the run.
"""

from ..pytestrail import PyTestRail

# this is the project id for the testrail project you're working with.  To find it, go to the main dashboard in
# testrail > select the project you want.  in the upper left of the resulting project overview tab you'll see an
# integer with a P in front of it.  That integer is that projects project_id.  In this example we're using the
# Embedded systems project_id which is 27.
project_id = 27

# this id is located in the upper left of the test suite page for the suite you want to use.  It starts with an S.
# leave the S off.
test_suite_id = 2552

# the user is what you use to log into test rail with.  The api key is either your password (dont use password though)
# or an api key for your user.  set up api keys by going into your user settings > api keys tab > add api key.
testrail_user = 'bzuck@control4.com'
testrail_api_key = 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.'

ptr = PyTestRail(testrail_user, testrail_api_key)

# create the test run, import all cases from the suite
response = ptr.add_run(project_id
            , test_suite_id
            , 'API run creation test 2'# required.  test run name
            , 'Test run created using the api.'# required.  test run description
            , include_all_cases=True# optional.  This is already defaulted to True i only included it here for visibility.  not required for this example
            # , milestone_id='Some meaningful milestone'# optional.  use if you want to link this test run to a milestone
            # , assignedto_id=152# optional.  use this if you want to assign the run to a particular user
            )
print('testrail response: {0}'.format(response))
