import argparse
from AutomationTools_master.testrail_api.pytestrail import PyTestRail

parser = argparse.ArgumentParser()
parser._action_groups.pop()
parser.add_argument('--project_id', default=None)
parser.add_argument('--suite_id', default=None)
parser.add_argument('--testrun_name', default=None)
parser.add_argument('--include_all_cases', default=None)
parser.add_argument("--list", nargs="+", default=["a", "b"])
args = parser.parse_args()


def testrailReport():
    testrailObj = PyTestRail('testautomation@snapone.com', 'EYDXwyN8BuZ3hwMIXBGN-2C.xsEiCCvkOWnZ/L89Y')
    # testrailObj = testrailClass.testrail_integration()
    return testrailObj


def testRunID():
    # args2 = parser.parse_args()
    testrailReport = testrailObj = PyTestRail('testautomation@snapone.com', 'EYDXwyN8BuZ3hwMIXBGN-2C.xsEiCCvkOWnZ/L89Y')
    project_id = args.project_id
    suite_id = args.suite_id
    test_run_name = args.testrun_name
    response2 = testrailReport.add_run(project_id
                                       , suite_id
                                       , test_run_name
                                       , 'Test run created using the TestRail.'  # required.  test run description
                                       , include_all_cases=args.include_all_cases
                                       , case_ids=args.list
                                       # optional.  This is already defaulted to True i only included it here for visibility.  not required for this example
                                       # , milestone_id='Some meaningful milestone'# optional.  use if you want to link this test run to a milestone
                                       # , assignedto_id=152# optional.  use this if you want to assign the run to a particular user
                                       )
    print('testrail response3: {}'.format(response2))
    testRunID = response2['id']
    return testRunID


if __name__ == "__main__":
    """create testrail run"""
    testRunID()
