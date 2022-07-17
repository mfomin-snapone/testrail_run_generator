from typing import List

from .pytestrail import PyTestRail, APIError, TestStatus
from ..common.helpers import Helpers as help
from typing import List, Dict


class TestTags():
    # Embedded systems tags for test cases.  If you're using this for a different testrail project then add tags
    # for that project instead
    Firmware = 1
    CLv2_gateway = 2
    CLv2_apd = 3
    CLv2_relay = 4
    CLv2_fpd = 5
    Disabled = 6
    Automated = 7
    Burninator = 8
    v_110 = 9
    v_220 = 10
    v_240 = 11
    v_277 = 12
    Hz_50 = 13
    Hz_60 = 14
    PLv1_gateway = 15
    PLv1_apd = 16
    PLv1_relay = 17
    PLv1_0_to_10v = 18
    Gen3i_SSW = 19

    VL_DIM = 38
    VL_SW = 39
    VL_ODIM = 40
    VL_OSW = 41

    Z2I0 = 44
    Z2C = 45


class Operator():
    """
    Case that defines the allowed operators for use in CaseFilter's.
    """
    isAnd = "&&"
    isOr = "||"
    isEqual = "=="
    isNotEqual = "!="


class CaseFilter():
    def __init__(self, operator # type: str
                 , tag_id       # type: int
                 ):
        assert isinstance(operator, str)
        assert isinstance(tag_id, int)
        self.operator = operator
        self.tag_id = tag_id


class TestCase:
    def __init__(self, number, title="",
                 test_run=None  # type: TestRun
                 ):
        self.number = number
        self.title = title
        self.results = {'pass': [], 'warning': [], 'fail': [], 'error': [], 'all': []}
        self.step_results = None
        self.step_result_start_indexes = None
        self.steps_updated_with_results = False
        self.custom_fields_dict = {}
        self.PASS = 0
        self.FAIL = 0
        self.ERROR = 0
        self.WARNING = 0
        self.testrail_comment = ''
        self.testrail_formatted_result = None
        self.test_run = test_run
        self.test_steps = None
        if isinstance(test_run, TestRun):
            self.test_steps = test_run.interface.get_case_steps(number, test_run.run_tests)

    def does_step_exist(self, step_name):
        # type: (str) -> bool
        """
        Checks to see if the string step name value exists in any of the test step dictionaries for this test case.
        If it does return True, if not return False
        :param step_name: string test step name to look for
        :return: bool depending on whether it found the step name or not.
        """
        if help.find_pair_in_list_of_dicts("content", step_name, self.test_steps, return_index=True) >= 0:
            return True
        else:
            return False

    def add_step_to_end(self, step_name):
        # type: (str) -> None
        """
        Adds a new test case step to the end of an existing list of test step dictionaries.
        :param step_name: string name of the test step you want to add.
        """
        new_step = {"content": step_name, "expected": ""}
        if self.test_steps is not None:
            self.test_steps.append(new_step)

    def save_current_result_indexes(self):
        self.step_result_start_indexes = {}
        for key, value in self.results.items():
            self.step_result_start_indexes.update({key: (len(value))})

    def get_current_step_results(self):
        step_results = {}
        for key, value in self.results.items():
            step_results.update({key: value[self.step_result_start_indexes[key]:]})
        return step_results

    def add_results_to_test_steps(self, step_name, test_status=TestStatus.PASSED):
        if self.test_steps is not None:
            step_results = self.get_current_step_results()
            for step in self.test_steps:
                if "content" in step:
                    if step["content"] == step_name:
                        # found the step, add results and status key value pairs
                        if "status_id" not in step:
                            step.update({"status_id": test_status})
                            self.steps_updated_with_results = True
                        else:
                            print("status_id already exists for this step: {}\r\nNot going to overwrite it.  "
                                        "check this out cause its most likely a bug.".format(step))
                        if step_results:
                            if "actual" not in step:
                                # step.update({"actual": step_results})
                                all_result_str = '\n'.join(step_results['all'])
                                step.update({"actual": all_result_str})
                                self.steps_updated_with_results = True
                            else:
                                print("'actual' key already exists in step: {}\r\nIt probably shouldn't be there "
                                            "unless you actually wanted to append results to the same step?  "
                                            "Check this out.".format(step))
                                # appending new step results to existing.
                                all_result_str = '\n'.join(step_results['all'])
                                step["actual"] = step["actual"] + all_result_str
                                self.steps_updated_with_results = True
                        break
                    # else:
                    #     raise ValueError("couldnt find dict entry 'content': {} in the self.test_steps dict: \r\n{}\r\n"
                    #                      "It needs to be there before getting here.".format(step_name, self.test_steps))
                else:
                    raise ValueError("key 'content' doesnt exist in the step dict.  This isn't a valid step.  "
                                     "step is: {}".format(step))
        else:
            raise ValueError("self.test_steps is None.  Cant add results to a blank set of steps.")


class TestRun():
    def __init__(self, suite_id             # type: str or int
                 , test_script_names        # type: List[str]
                 , case_filter_list=None    # type: List[CaseFilter]
                 , run_id=""                # type: str or int
                 , interface=None           # type: PyTestRail
                 , project_id=27            # type: str or int
                 , run_header=None          # type: dict
                 , run_tests=None           # type: List[dict]
                 , include_case_ids=None    # type: List[str or int]
                 ):
        # check args
        if include_case_ids is None:
            include_case_ids = []
        assert isinstance(suite_id, (str, int))
        assert isinstance(test_script_names, list)
        if case_filter_list != None:
            assert isinstance(case_filter_list, list)
            for case_filter in case_filter_list:
                assert isinstance(case_filter, CaseFilter)
        assert isinstance(run_id, (str, int))
        if interface:
            assert isinstance(interface, PyTestRail)
        # assert isinstance(project_id, str)
        assert isinstance(include_case_ids, list)

        self.suite_id = PyTestRail.strip_id(suite_id)
        self.test_script_names = test_script_names
        self.case_filter_list = case_filter_list
        self.run_id = run_id
        self.interface = interface
        self.project_id = project_id
        self.run_name = ""
        self.update_after_each_testcase = True
        self.run_header = run_header
        self.run_tests = run_tests
        self.include_case_ids = include_case_ids
        if self.include_case_ids:
            self.strip_case_ids()

    def strip_case_ids(self):
        if self.include_case_ids:
            for index, item in enumerate(self.include_case_ids):
                self.include_case_ids[index] = PyTestRail.strip_id(item)

    @staticmethod
    def run_from_existing_runID(testrun_id, interface):
        # type: (str or int, PyTestRail) -> TestPlan
        run_id = interface.strip_id(testrun_id)
        run_data = interface.get_run(run_id)
        if run_data:
            project_id = run_data["project_id"]
            suite_id = run_data["suite_id"]
            run_name = run_data["name"]
            test_run = TestRun(suite_id, [""], run_id=run_id, interface=interface, project_id=project_id
                               , run_header=run_data)
            test_run.run_name = str(run_name)
            test_run.run_tests = interface.get_tests_in_run(testrun_id)
            return test_run
        else:
            raise ValueError('testrun_id: {0} doesn''t exist in testrail.'.format(testrun_id))

    @staticmethod
    def run_from_add_run_response(add_run_response, interface):
        # type: (str or int, PyTestRail) -> TestPlan
        if add_run_response:
            run_id = add_run_response["id"]
            project_id = add_run_response["project_id"]
            suite_id = add_run_response["suite_id"]
            run_name = add_run_response["name"]
            test_run = TestRun(suite_id, [""], run_id=run_id, interface=interface, project_id=project_id
                               , run_header=add_run_response)
            test_run.run_tests = interface.get_tests_in_run(run_id)
            test_run.run_name = str(run_name)
            return test_run
        else:
            raise ValueError('the add_run_response is blank.  This doesnt work without a valid response form an '
                             'add_run command.  Consider using the run_from_existing_runID command instead.')

    def establish_connection(self, interface_user=None, interface_pwd=None):
        """
        Used to instantiate a pytestrail interface connection if one doesnt already exist.  Normally, an existing
        connection will be passed in.  This is for cases where an interface connection was not already established
        upstream somewhere.
        :param interface_user: string user id
        :param interface_pwd: string password
        """
        if help.check_arg_types("establish_connection", [[interface_user, (str, None)], [interface_pwd, (str, None)]]):
            # only instantiate a new testrail connection if one isn't already passed into TestRun.
            if not isinstance(self.interface, PyTestRail):
                # default user_id and user_key if none are passed in.
                user_id = "bzuck@control4.com"
                user_key = "Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt."
                if interface_user and interface_pwd:
                    # values for user and key were passed in so use those for the connection
                    user_id = interface_user
                    user_key = interface_pwd
                if not isinstance(self.interface, PyTestRail):
                    try:
                        self.interface = PyTestRail(user_id, user_key)
                    except APIError as error:
                        print(error)
                    else:
                        self.is_interface_initialized = True


    def format_testrail_result(self, finised_testcase, test_case_pass, result_type):
        # type: (TestCase, bool, str) -> dict
        """
        uses PyTestRail.result_builder to build a properly formatted testrail test case result that the api
        can consume.
        :param finished_testcase: type reporter.TestCase.  This is the finished TestCase object for the test case
            we're working on currently.
        :param test_case_pass: bool.  True if pass, False if fail.
        :return: formatted test result ready for pytestrail.add_test_results to consume.
        """
        if not self.interface:
            raise APIError('PyTestRail isn''t initialized.  Need to make sure an instantiated PyTestRail object gets '
                           'passed to TestRun.interface before the code gets to here')
        good_result_types = ['ALL', 'GROUPED']
        if result_type == '':
            result_type = 'ALL'
        elif result_type.upper() not in good_result_types:
            raise ValueError('invalid result type.  I got: {0}.  valid values are nothing or {1}'
                             .format(result_type, good_result_types))

        testrail_comment = self.format_result_comment(finised_testcase, result_type)
        if test_case_pass:
            pass_status = self.interface.test_status.PASSED
        else:
            pass_status = self.interface.test_status.FAILED

        testrail_formatted_result = self.interface.result_builder(
            self.interface.strip_id(finised_testcase.number)
            , pass_status
            , testrail_comment
            , custom_fields_dict=finised_testcase.custom_fields_dict
            )
        return testrail_formatted_result


    @staticmethod
    def format_result_comment(finished_testcase, result_type):
        """
        formats the testrail test result comment.  This is where we put the zpyclient test results for all tests
        between the testcase start and testcase end commands.
        :param finished_testcase: type reporter.TestCase.  This is the finished TestCase object for the test case
            we're working on currently.
        :return: string of the comment we want to show in testrail for the testcase in question
        """
        if result_type.upper() == 'GROUPED':
            case_comment = 'PASS: {0}\r\n' \
                           'WARNING: {1}\r\n' \
                           'FAIL: {2}\r\n' \
                           'ERROR: {3}\r\n\r\n' \
                           'Details:\r\n' \
                           'Passed:\r\n{4}\r\n\r\n' \
                           'Warnings:\r\n{5}\r\n\r\n' \
                           'Failed:\r\n{6}\r\n\r\n' \
                           'Errors:\r\n{7}'.format(finished_testcase.PASS
                                                   , finished_testcase.WARNING
                                                   , finished_testcase.FAIL
                                                   , finished_testcase.ERROR
                                                   # , finished_case.results['pass']
                                                   , '\n'.join(finished_testcase.results['pass'])
                                                   , '\n'.join(finished_testcase.results['warning'])
                                                   , '\n'.join(finished_testcase.results['fail'])
                                                   , '\n'.join(finished_testcase.results['error'])
                                                   )
        elif result_type == 'ALL':
            case_comment = 'PASS: {0}\r\n' \
                           'WARNING: {1}\r\n' \
                           'FAIL: {2}\r\n' \
                           'ERROR: {3}\r\n\r\n' \
                           'Details:\r\n{4}'.format(finished_testcase.PASS
                                                    , finished_testcase.WARNING
                                                    , finished_testcase.FAIL
                                                    , finished_testcase.ERROR
                                                    , '\n'.join(finished_testcase.results['all'])
                                                    )
        return case_comment



class TestPlan():
    def __init__(self
                 , test_runs_list       # type: List[TestRun]
                 , add_plan_response    # type: dict
                 , product_name         # type: str
                 , product_mac          # type: str
                 , product_family       # type: str
                 , firmware_version     # type: str
                 , interface            # type: PyTestRail
                 ):
        # check args
        assert isinstance(test_runs_list, list)
        assert len(test_runs_list) > 0
        for test_run in test_runs_list:
            assert isinstance(test_run, TestRun)
        assert isinstance(add_plan_response, dict)
        assert isinstance(product_name, str)
        assert isinstance(product_mac, str)
        assert isinstance(product_family, str)
        assert isinstance(firmware_version, str)
        assert isinstance(interface, PyTestRail)

        self.test_runs_list = test_runs_list
        self.add_plan_response = add_plan_response
        self.product_name = product_name
        self.product_mac = product_mac
        self.product_family = product_family
        self.firmware_version = firmware_version
        self.interface = interface
        self.name = ""
        self.plan_id = 0
        self.added_runs = []
        self.parse_plan_response()

    def parse_plan_response(self):
        if self.add_plan_response:
            if self.__length_check():
                self.plan_id = self.add_plan_response['id']
                self.name = self.add_plan_response['name']
                self.description = str(self.add_plan_response['description'])
                for idx in range(0, len(self.added_runs)):
                    if self.test_runs_list[idx].suite_id == self.added_runs[idx]['suite_id']:
                        self.test_runs_list[idx].run_id = self.added_runs[idx]['id']
                    else:
                        raise ValueError("suite id mismatch at index {}.  we expect id {} but got {}.  The suite id "
                                         "for the run we wanted to add doesnt match what was added.  This indicates "
                                         "a problem with either what was sent to the add_plan command or maybe "
                                         "testrail isnt returning the added runs in the same order they were passed "
                                         "in anymore ".format(idx, self.test_runs_list[idx].suite_id
                                                              , self.added_runs[idx]['suite_id']))
        else:
            raise ValueError("The add_plan_response passed into TestPlan is blank.  I received: {}"
                             .format(self.add_plan_response))

    def __length_check(self):
        if self.test_runs_list and self.add_plan_response:  # make sure both are populated
            expected_length = len(self.test_runs_list)
            add_plan_length = 0
            for entry in self.add_plan_response["entries"]:
                for run in entry['runs']:
                    add_plan_length += 1
                    self.added_runs.append(run)
            if expected_length == add_plan_length:
                return True
            else:
                raise ValueError("**CRITICAL**  The number of runs we expected to get added to the test plan when "
                                 "it was created is different than the number that actually got added.  We expected "
                                 "{}, we got {}.  Fix this and try again".format(expected_length, add_plan_length))
        else:
            raise ValueError("Both self.test_runs_list and self.add_plan_response need to have length > 0 for "
                             "__length_check to work.  their lengths are {} and {} respectively"
                             .format(len(self.test_runs_list), len(self.add_plan_response)))

    @staticmethod
    def plan_from_existing_runID(testrun_id):
        # type: (str) -> TestPlan
        pass


if __name__ == '__main__':
    add_plan_response = {u'is_completed': False, u'custom_status3_count': 0, u'created_on': 1581614559, u'retest_count': 0, u'id': 5233, u'created_by': 45, u'passed_count': 0, u'project_id': 27, u'custom_status6_count': 0, u'failed_count': 0, u'description': u'programatically added plan 1 description', u'custom_status5_count': 0, u'entries': [{u'runs': [{u'include_all': True, u'is_completed': False, u'custom_status3_count': 0, u'created_on': 1581614559, u'entry_id': u'9d826640-37a0-4275-9d63-f2fe8f01d893', u'retest_count': 0, u'id': 5234, u'plan_id': 5233, u'created_by': 45, u'passed_count': 0, u'project_id': 27, u'config': None, u'custom_status6_count': 0, u'failed_count': 0, u'description': u'programatically added run 1 description', u'custom_status5_count': 0, u'suite_id': 2552, u'milestone_id': None, u'name': u'programatically added run 1', u'assignedto_id': None, u'blocked_count': 0, u'completed_on': None, u'config_ids': [], u'url': u'https://testrail.control4.com/index.php?/runs/view/5234', u'custom_status4_count': 0, u'untested_count': 16, u'custom_status2_count': 0, u'entry_index': 1, u'custom_status1_count': 0, u'custom_status7_count': 0}], u'suite_id': 2552, u'id': u'9d826640-37a0-4275-9d63-f2fe8f01d893', u'name': u'programatically added run 1'}, {u'runs': [{u'include_all': True, u'is_completed': False, u'custom_status3_count': 0, u'created_on': 1581614559, u'entry_id': u'515d9ecf-1060-4e28-8a80-e57af86e4060', u'retest_count': 0, u'id': 5235, u'plan_id': 5233, u'created_by': 45, u'passed_count': 0, u'project_id': 27, u'config': None, u'custom_status6_count': 0, u'failed_count': 0, u'description': u'programatically added run 2 description', u'custom_status5_count': 0, u'suite_id': 2684, u'milestone_id': None, u'name': u'programatically added run 2', u'assignedto_id': None, u'blocked_count': 0, u'completed_on': None, u'config_ids': [], u'url': u'https://testrail.control4.com/index.php?/runs/view/5235', u'custom_status4_count': 0, u'untested_count': 411, u'custom_status2_count': 0, u'entry_index': 2, u'custom_status1_count': 0, u'custom_status7_count': 0}], u'suite_id': 2684, u'id': u'515d9ecf-1060-4e28-8a80-e57af86e4060', u'name': u'programatically added run 2'}, {u'runs': [{u'include_all': True, u'is_completed': False, u'custom_status3_count': 0, u'created_on': 1581614559, u'entry_id': u'5dd55cc2-1808-4aca-8cb6-20a9295871c8', u'retest_count': 0, u'id': 5236, u'plan_id': 5233, u'created_by': 45, u'passed_count': 0, u'project_id': 27, u'config': None, u'custom_status6_count': 0, u'failed_count': 0, u'description': u'programatically added run 3 description', u'custom_status5_count': 0, u'suite_id': 2684, u'milestone_id': None, u'name': u'programatically added run 3', u'assignedto_id': None, u'blocked_count': 0, u'completed_on': None, u'config_ids': [], u'url': u'https://testrail.control4.com/index.php?/runs/view/5236', u'custom_status4_count': 0, u'untested_count': 411, u'custom_status2_count': 0, u'entry_index': 3, u'custom_status1_count': 0, u'custom_status7_count': 0}], u'suite_id': 2684, u'id': u'5dd55cc2-1808-4aca-8cb6-20a9295871c8', u'name': u'programatically added run 3'}], u'milestone_id': None, u'name': u'programatically added test plan 1', u'assignedto_id': None, u'blocked_count': 0, u'completed_on': None, u'url': u'https://testrail.control4.com/index.php?/plans/view/5233', u'custom_status4_count': 0, u'untested_count': 838, u'custom_status2_count': 0, u'custom_status1_count': 0, u'custom_status7_count': 0}

    # plan_entries = []
    # plan_entries.append(TestRun("S2552", "valueLighting_Outlet_Switch_auto.txt"))
    # plan_entries.append(TestRun("S2684", "valueLighting_Outlet_Switch_manual.txt"))
    # plan_entries.append(TestRun("S2684", "valueLighting_Outlet_Switch_manual.txt"))
    #
    #
    # tp = TestPlan(plan_entries, add_plan_response,'widget 1', '000d6ffffecd6ca3', 'widgets', '1.05.63')

    x=1
    TestRun.run_from_existing_runID(5462)

