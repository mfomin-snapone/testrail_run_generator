import argparse

from testrail import *
from AutomationTools_master.testrail_api.pytestrail import PyTestRail
import pytest

client = APIClient('https://testrail.control4.com/')
client.user = 'testautomation@snapone.com'
client.password = 'EYDXwyN8BuZ3hwMIXBGN-2C.xsEiCCvkOWnZ/L89Y'

parser = argparse.ArgumentParser()
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')
optional.add_argument('--project_id', default=None)
optional.add_argument('--suite_id', default=None)
optional.add_argument('--testrun_name', default=None)
optional.add_argument('--case_ids', default=None)
args = parser.parse_args()


"""parse cli args"""
parser = argparse.ArgumentParser()
parser.add_argument('project_id')
parser.add_argument('suite_id')
parser.add_argument('testrun_name')
parser.add_argument('case_ids', type=int, help='project_id with BDD suite')
parser.add_argument('-r', required=False, nargs='?', const=False, default=True, type=bool, help="if you don't want to send reports to testrailand datalake") #nargs=1,
#parser.add_argument('-s', metavar='suite_id', nargs=1, required=False, type=str, help='suite_id if you want create testrun based on it')
parser.add_argument('-c', required=False, type=str, help='execute testrail command api, ex. -c get_statuses or -c get_test/4514653')


@pytest.fixture(scope='session')
def testrailReport():
    testrailObj = PyTestRail('testautomation@snapone.com', 'EYDXwyN8BuZ3hwMIXBGN-2C.xsEiCCvkOWnZ/L89Y')
    # testrailObj = testrailClass.testrail_integration()
    return testrailObj


@pytest.fixture(scope='session')
def testRunID(testrailReport):
    project_id = args.project_id
    suite_id = args.suite_id
    test_run_name = args.testrun_name
    response2 = testrailReport.add_run(project_id
                                       , suite_id
                                       , test_run_name
                                       , 'Test run created using the TestRail.'  # required.  test run description
                                       , include_all_cases=False
                                       , case_ids=[args.case_ids]
                                       # optional.  This is already defaulted to True i only included it here for visibility.  not required for this example
                                       # , milestone_id='Some meaningful milestone'# optional.  use if you want to link this test run to a milestone
                                       # , assignedto_id=152# optional.  use this if you want to assign the run to a particular user
                                       )
    print('testrail response3: {}'.format(response2))
    testRunID = response2['id']
    return testRunID
