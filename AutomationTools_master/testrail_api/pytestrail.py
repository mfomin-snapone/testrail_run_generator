# Author: Bryan Zuck 09/2019
# Control4 Confidential and Proprietary Information
try:
    from .testrail import APIClient, APIError
except:
    from .testrail import APIClient, APIError

from typing import List, Dict, Text, Optional
import time
import logging

try:
    from ..common.helpers import Helpers
except:
    # If running in zpyclient your python path is not correct this will fail
    # path should have ~/<PATHTOZPYCLIENT>/plugins/AutomationTools/
    # but here is a work around
    from ..common.helpers import Helpers


class TestStatus:
    PASSED = 1
    BLOCKED = 2
    UNTESTED = 3
    RETEST = 4
    FAILED = 5


class PyTestRail(APIClient):
    # inherit from testrail's APIClient class.
    def __init__(self, username, api_key, testrail_url='https://testrail.control4.com/'):
        """
        pass in the username and api_key(password) for the testrail user.  The testrail url wont change for anyone
        in the company so i hard coded it here but you can override it if you want.  Then call the APIClient constructor
        and set the required username and password.  At this point you can get and send data from testrail.
        :type username: str
        :type api_key: str
        :type testrail_url: str
        :param username: the testrail username to use...eg user@control4.com
        :param api_key: the testrail api_key or password for the user.  you can add API_keys for your user in account
                        settings in testrail.  Make sure you hit save settings first or they wont work.
        :param testrail_url: url to the testrail instance you're working with.
        """
        APIClient.__init__(self, testrail_url)
        self.user = username
        self.password = api_key
        self.test_status = TestStatus()
        self.help = Helpers()

    @property
    def get_projects(self):
        """
        returns json with all existing projects in testrail.
        :return:  list of project dictionaries.  See get_project return description
        """
        try:
            projects = self.send_get('get_projects')
        except APIError as error:
            print(error)
        else:
            return projects

    def get_project(self, project_id):
        """
        gets details about a particular project (suite) from testrail.
        :type project_id: int
        :param project_id:
        :return: dict with the following elements:
            Name	            Type	    Description
            announcement	    string	    The description/announcement of the project
            completed_on	    int	        The date/time when the project was marked as completed (as UNIX timestamp)
            id	                int	        The unique ID of the project
            is_completed	    bool	    True if the project is marked as completed and false otherwise
            name	            string	    The name of the project
            show_announcement	bool	    True to show the announcement/description and false otherwise
            suite_mode	        integer	    The suite mode of the project (1 for single suite mode, 2 for single suite
                                            + baselines, 3 for multiple suites) (added with TestRail 4.0)
            url	                string	    The address/URL of the project in the user interface
        """
        try:
            project = self.send_get('get_project/{0}'.format(project_id))
        except APIError as error:
            print(error)
        else:
            return project

    def get_project_id(self, project_name):
        """
        returns an integer project id for a project with a given project name.
        :type project_name: str
        :param project_name: string of the project name as it exists in test rail.  Case sensative
        """
        try:
            projects = self.get_projects
            project_id = -1
            for project in projects:
                if project['name'] == project_name:
                    project_id = project['id']
                    break
        except APIError as error:
            print(error)
        else:
            return project_id

    def get_suites(self, project_id):
        """
        returns header level data for each test suite for a given project id
        :type project_id: int
        :param project_id: integer project id
        :return: list of dictionaries containing data for each suite.  See the return description for get_suite
        """
        try:
            suites = self.send_get('get_suites/{0}'.format(project_id))
        except APIError as error:
            print(error)
        else:
            return suites

    def get_suite(self, suite_id):
        """
        gets header level data for a test suite with given suite id
        :type suite_id: int
        :param suite_id:
        :return: dict with the following elements
            Name	            Type	    Description
            completed_on	    timestamp	The date/time when the test suite was closed (as UNIX timestamp)
            description	        string	    The description of the test suite
            id	                int	        The unique ID of the test suite
            is_baseline	        bool	    True if the test suite is a baseline test suite and false otherwise
            is_master	        bool	    True if the test suite is a master test suite and false
            name	            string	    The name of the test suite
            project_id	        int	        The ID of the project this test suite belongs to
            url	                string	    The address/URL of the test suite in the user interface
        """
        try:
            project = self.send_get('get_suite/{0}'.format(suite_id))
        except APIError as error:
            print(error)
        else:
            return project

    def get_suite_id(self, project_id, suite_name):
        """
        returns an integer suite id for a given suite name of a given project id.
        :type project_id: int
        :type suite_name: str
        :param project_id: integer project id
        :param suite_name: string suite name you're looking for
        :return:
        """
        try:
            suites = self.get_suites(project_id)
            suite_id = -1
            for suite in suites:
                if suite['name'] == suite_name:
                    suite_id = suite['id']
                    break
        except APIError as error:
            print(error)
        else:
            return suite_id

    def add_suite(self, project_id, suite_name, description):
        """
        """
        """
        adds a suite to a given project.  You can only give it a name and description through the api.
        :type project_id: int
        :type suite_name: str
        :type description: str
        :param project_id: id for the project you want to add a suite to
        :param suite_name: name for the new suite
        :param description: description of the new suite
        :return:
        """
        suite_data = {
            "name": suite_name,
            "description": description
        }
        try:
            response = self.send_post('add_suite/{0}'.format(project_id), suite_data)
        except APIError as error:
            print(error)
        else:
            return response

    def update_suite(self, suite_id, suite_name=None, description=None):
        """
        updates a suite's description or name.  suite_name and description are defaulted to None so you can pass in
        one or the other or both.  It will only update them if they're populated.
        :type suite_id: int
        :type suite_name: str
        :type description: str
        :param suite_id: suite id you want to update
        :param suite_name: new suite name.  Can be passed in by itself
        :param description: new suite description.  Can be passed in by itself
        :return:
        """
        suite_data = {}
        # since this is update we only want to post name or description if they've been passed in.  default vavlue is
        # None.  So if the user only wants to update the description, it wont pass in a new value for name too.
        if suite_name is not None:
            suite_data.update({'name': suite_name})
        if description is not None:
            suite_data.update({'description': description})
        # only update if the user passed in a value for suite_name or description of both.
        if len(suite_data) > 0:
            try:
                response = self.send_post('update_suite/{0}'.format(suite_id), suite_data)
            except APIError as error:
                print(error)
            else:
                return response
        else:
            raise ValueError("length of update post dict is 0.  pass in a value for suite name or description or both")

    def delete_suite(self, suite_id):
        """
        Deletes a test suite.  DO NOT USE THIS LIGHTLY.  It cannot be undone and removes all history of test runs
        for this suite.  Be darn sure you know what you're doing before calling this.
        :type suite_id: int
        :param suite_id: id for the suite you want to delete.
        :return:
        """
        try:
            print('deleting suite id: {0}.'.format(suite_id))
            response = self.send_post('delete_suite/{0}'.format(suite_id), {})
        except APIError as error:
            print(error)
        else:
            return response

    def get_runs(self, project_id, created_after=None, created_before=None, created_by=None, is_completed=None,
                 limit=None, offset=None, milestone_id=None, suite_id=None):
        """
        Gets header level details for each test run in a given project.
        :type project_id: int
        :type created_after: timestamp
        :type created_before: timestamp
        :type created_by: list
        :type is_completed: bool
        :type limit: int
        :type offset: int
        :type milestone_id: list
        :type suite_id: list
        :param project_id: Required. project id you want to retrieve test run data from.
        :param created_after: Optional.  Only return test runs created after this date (as UNIX timestamp).
        :param created_before: Optional.  Only return test runs created before this date (as UNIX timestamp).
        :param created_by: 	Optional.  A comma-separated INTEGER list of creators (user IDs) to filter by.
        :param is_completed: Optional.  True to return completed test runs only. False to return active test runs only.
        :param limit: Optional.  Limit the result to :limit number of test runs.
        :param offset: Optional  Skip the first :offset number of records.  The system will only ever return a max of
                       250 results so you have to use this to get the next set if you want more than 250.
        :param milestone_id: Optional.  A comma-separated INTEGER list of milestone IDs to filter by.
        :param suite_id: Optional.  A comma-separated INTEGER list of test suite IDs to filter by.
        :return: returns a list of dicts containing the same data as get run.  see that for details on what each
                 dict contains.
        """
        command = 'get_runs/{0}'.format(project_id)
        # add optional args to command.  Only add one's whose value is not None (which is the default)
        if created_after is not None:
            command = self.add_argument(command, 'created_after={0}'.format(created_after))
        if created_before is not None:
            command = self.add_argument(command, 'created_before={0}'.format(created_before))
        if created_by is not None:
            command = self.add_argument(command, 'created_by={0}'.format(','.join(str(x) for x in created_by)))
        if is_completed is not None:
            command = self.add_argument(command, 'is_completed={0}'.format(is_completed))
        if limit is not None:
            command = self.add_argument(command, 'limit={0}'.format(limit))
        if offset is not None:
            command = self.add_argument(command, 'offset={0}'.format(offset))
        if milestone_id is not None:
            command = self.add_argument(command, 'milestone_id={0}'.format(','.join(str(x) for x in milestone_id)))
        if suite_id is not None:
            command = self.add_argument(command, 'suite_id={0}'.format(','.join(str(x) for x in suite_id)))

        try:
            response = self.send_get(command)
        except APIError as error:
            print(error)
        else:
            return response

    def get_run(self, run_id):
        # type: (str or int) -> dict
        """
        gets header level data about a test run of a given id.
        :type run_id: str or int
        :param run_id: test run id in question.  If you use get_runs to find the run you want then the field
         you're looking in that result set is called id
        :return: dict with the following elements
            Name	            Type	    Description
            assignedto_id	    int	        The ID of the user the entire test run is assigned to
            blocked_count	    int	        The amount of tests in the test run marked as blocked
            completed_on	    timestamp	The date/time when the test run was closed (as UNIX timestamp)
            config	            string	    The configuration of the test run as string (if part of a test plan)
            config_ids	        array	    The array of IDs of the configurations of the test run (if part of a
                                            test plan)
            created_by	        int	        The ID of the user who created the test run
            created_on	        timestamp	The date/time when the test run was created (as UNIX timestamp)
            custom_status?_count int	    The amount of tests in the test run with the respective custom status
            description	        string	    The description of the test run
            failed_count	    int	        The amount of tests in the test run marked as failed
            id	                int	        The unique ID of the test run
            include_all	        bool	    True if the test run includes all test cases and false otherwise
            is_completed	    bool	    True if the test run was closed and false otherwise
            milestone_id	    int	        The ID of the milestone this test run belongs to
            plan_id	            int	        The ID of the test plan this test run belongs to
            name	            string	    The name of the test run
            passed_count	    int	        The amount of tests in the test run marked as passed
            project_id	        int	        The ID of the project this test run belongs to
            retest_count	    int	        The amount of tests in the test run marked as retest
            suite_id	        int	        The ID of the test suite this test run is derived from
            untested_count	    int	        The amount of tests in the test run marked as untested
            url	                string	    The address/URL of the test run in the user interface
        """
        if self.help.check_arg_types("get_run", [[run_id, (str, int)]]):
            run_id_int = self.strip_id(run_id)
            try:
                response = self.send_get('get_run/{0}'.format(run_id_int))
            except APIError as error:
                print(error)
            else:
                return response

    def is_case_in_run(self, case_id, run_id):
        # type: (str or int, str or int) -> bool
        """

        :param case_id:
        :param run_id:
        :return:
        """
        if self.help.check_arg_types("is_caseId_in_run", [[case_id, (str, int)], [run_id, (str, int)]]):
            case_id_int = self.strip_id(case_id)
            run_id_int = self.strip_id(run_id)
            tests_in_run = self.get_tests_in_run(run_id_int)
            # use list comprehension to quickly loop through tests and see if the case id is present.  If so, return
            # True.  if not, return False
            for results_dict in [x for x in tests_in_run if x["case_id"] == case_id_int]:
                # return results_dict["run_id"]
                return True
            return False

    def get_proj_suite_from_run(self, testrun_id):
        run_id = self.strip_id(testrun_id)
        run_data = self.get_run(run_id)
        if run_data:
            return run_data['project_id'], run_data['suite_id']
        else:
            raise ValueError('testrun_id: {0} doesn''t exist in testrail.  check the use_testrun_id command and '
                             'make sure a valid run id is there.'.format(run_id))

    def get_runid_for_case_in_plan(self, case_id, plan_id):
        if self.help.check_arg_types("get_runid_for_case_in_plan", [[case_id, (str, int)], [plan_id, (str, int)]]):
            case_id_int = self.strip_id(case_id)
            plan_id_int = self.strip_id(plan_id)
            print("before get plan")
            plan_data = self.get_plan(plan_id_int)
            print("after get plan")
            for entry in plan_data["entries"]:
                for run in entry["runs"]:
                    if self.is_case_in_run(case_id_int, run["id"]):
                        return run["id"]
            return None

    def add_run(self, project_id, suite_id, name, description, include_all_cases=True, case_ids=None,
                milestone_id=None, assignedto_id=None):
        """
        adds a test run for a given project and and suite id.
        :type project_id: int
        :type suite_id: int
        :type name: str
        :type description: str
        :type include_all_cases: bool
        :type case_ids: list
        :type milestone_id: int
        :type assignedto_id: int
        :param project_id: required.  project id you want to add a test run to.
        :param suite_id: required.  suite containing the test cases you want in the run. If include_all_cases=True
                        then all cases from this suite will be imported.  If include_all_cases=False then also pass
                        in case_ids which is a list of integer test case id's that you want in the test run.
        :param name: required.  string name of the test run.
        :param description: required.  string description of the test run
        :param include_all_cases: optional.  bool that controls whether all cases from the provided suite id get
                                imported into the run or not.  If not, it imports those devined in case_ids
        :param case_ids: optional.  list of integer test case id's from the given suite that you want imported
                        into the run
        :param milestone_id: optional.  The integer ID of the milestone to link to the test run
        :param assignedto_id: The integer id for the user you want the test run assigned to.
        :return: dict with header level info on the new run created.  return type is the same as get_run.  see that
                for details.
        """
        # add required args first
        run_data = {
            'suite_id': suite_id
            , 'name': name
            , 'description': description
            , 'include_all': include_all_cases
        }
        # add optional args to run_data.  Only add one's whose value is not None (which is the default)
        if case_ids is not None:
            run_data.update({'case_ids': case_ids})
        if milestone_id is not None:
            run_data.update({'milestone_id': milestone_id})
        if assignedto_id is not None:
            run_data.update({'assignedto_id': assignedto_id})

        try:
            response = self.send_post('add_run/{0}'.format(project_id), run_data)
        except APIError as error:
            print(error)
        else:
            return response

    def update_run(self, run_id, name=None, description=None, include_all_cases=None, case_ids=None
                   , milestone_id=None):
        """
        updates a test run's header data.  Can also change which cases are included by passing in an array of integer
        case_ids and setting include_all_cases to False.
        :type run_id: int
        :type name: str
        :type description: str
        :type include_all_cases: bool
        :type case_ids: list
        :type milestone_id: int
        :param run_id: integer run id of the test run you want to update
        :param name: string name of the test run
        :param description: string description of the test run
        :param include_all_cases: bool indicating whether all cases from the parent suite are included in teh run
                                   or not.
        :param case_ids: an INTEGER array of case id's in the test run.  Use this if you want to change the test
                        cases in the test run.  include_all_cases needs to be set to false for this to work.
        :param milestone_id: the integer id of the milestone to link to the test run
        :return: same return type and data as get_run.  see that for details
        """
        run_data = {}
        if name is not None:
            run_data.update({'name': name})
        if description is not None:
            run_data.update({'description': description})
        if include_all_cases is not None:
            run_data.update({'include_all': include_all_cases})
        if case_ids is not None:
            run_data.update({'case_ids': case_ids})
        if milestone_id is not None:
            run_data.update({'milestone_id': milestone_id})

        print(run_data)
        if len(run_data) > 0:
            try:
                response = self.send_post('update_run/{0}'.format(run_id), run_data)
            except APIError as error:
                print(error)
            else:
                return response
        else:
            raise ValueError("length of update run dict is 0.  pass in at least one value to send the update")

    def close_run(self, run_id):
        """
        Closes a test run with a given run id and archives its tests and results.  This is irreversable so
        make sure this is what you want before you do it.
        :type run_id: int
        :param run_id: integer run id you want to close
        :return: returns a dict in the same format as get_run. see that for details.
        """
        try:
            response = self.send_post('close_run/{0}'.format(run_id), {})
        except APIError as error:
            print(error)
        else:
            return response

    def delete_run(self, run_id):
        """
        Deletes a test run of a given id.  This removes the run and all archived test results for the run permenantly
        use only if you're absolultely sure you dont need the data anymore.  It is irreversable.
        :type run_id: int
        :param run_id: run id you want to delete
        :return:
        """
        try:
            response = self.send_post('delete_run/{0}'.format(run_id), {})
        except APIError as error:
            print(error)
        else:
            return response

    def get_test(self, test_id):
        # type: (str or int) -> dict
        """
        gets details for a test in testrail.
        :param test_id: string or integer id of the test you want to look up.
        :return: Dict with the following fields.  see example below as well.

        The following system fields are always included in the response:

            Name	            Type	    Description
            assignedto_id	    int	        The ID of the user the test is assigned to
            case_id	            int	        The ID of the related test case
            estimate	        timespan	The estimate of the related test case, e.g. "30s" or "1m 45s"
            estimate_forecast	timespan	The estimate forecast of the related test case, e.g. "30s" or "1m 45s"
            id	                int	        The unique ID of the test
            milestone_id	    int	        The ID of the milestone that is linked to the test case
            priority_id	        int	        The ID of the priority that is linked to the test case
            refs	            string	    A comma-separated list of references/requirements that are linked to the test case
            run_id	            int	        The ID of the test run the test belongs to
            status_id	        int	        The ID of the current status of the test, also see get_statuses
            title	            string	    The title of the related test case
            type_id	            int	        The ID of the test case type that is linked to the test case

        example:
        {
            "assignedto_id": 1,
            "case_id": 1,
            "custom_expected": "..",
            "custom_preconds": "..",
            "custom_steps_separated": [
                {
                    "content": "Step 1",
                    "expected": "Expected Result 1"
                },
                {
                    "content": "Step 2",
                    "expected": "Expected Result 2"
                }
            ],
            "estimate": "1m 5s",
            "estimate_forecast": null,
            "id": 100,
            "priority_id": 2,
            "run_id": 1,
            "status_id": 5,
            "title": "Verify line spacing on multi-page document",
            "type_id": 4
        }
        """
        if self.help.check_arg_types("get_test", [[test_id, (str, int)]]):
            test_id_int = self.strip_id(test_id)
            try:
                response = self.send_get('get_test/{0}'.format(test_id_int))
            except APIError as error:
                print(error)
            else:
                return response

    def get_tests_in_run(self, run_id):
        # type: (str or int) -> List[dict]
        """
        returns a list dict's for all tests in a run.  The dict format is the same as the get_test response dict.
        :param run_id: string or integer id of the test run
        :return: list of get_test response dicts.  see the get_test method documentation for info.
        """
        if self.help.check_arg_types("get_tests", [[run_id, (str, int)]]):
            run_id_int = self.strip_id(run_id)
            try:
                response = self.send_get('get_tests/{0}'.format(run_id_int))
            except APIError as error:
                print(error)
            else:
                return response

    def get_results(self, test_id, limit=None, offset=None, status_id=None):
        """
        Returns a list of results for a given test id.  Up to 250 results per query.  This includes all historical
        results for this test id regardless of test run.  If there are more than 250 you need to run this multiple
        times using the offset arg.  for example, if there are 650 total results you would need to run this 3 times
        and concatenate the results.  First with no offset, second with offset at 250 and third with offset at 500.
        :type test_id: int
        :type limit: int
        :type offset: int
        :type status_id: list
        :param test_id: id of the test you want records for.
        :param limit: limit the number of reults to the first limit number of records.  if you want the first 20
                      then set limit=20
        :param offset: used to skip records.  if you want to skip the first 100 then send offset=100.
        :param status_id: list of integer status id'd you want to filter on.  the list is or'd so if you send [4,5]
                        you will get results with statuses of either 4 or 5 (retest, failed)
        :return: returns a list of dict's.  each dict contains at least the following elements:
            Name	            Type	    Description
            assignedto_id	    int	        The ID of the assignee (user) of the test result
            comment	            string	    The comment or error message of the test result
            created_by	        int	        The ID of the user who created the test result
            created_on	        timestamp	The date/time when the test result was created (as UNIX timestamp)
            defects	            string	    A comma-separated list of defects linked to the test result
            elapsed	            timespan	The amount of time it took to execute the test (e.g. "1m" or "2m 30s")
            id	                int	        The unique ID of the test result
            status_id	        int	        The status of the test result, e.g. passed or failed, also see get_statuses
            test_id	            int	        The ID of the test this test result belongs to
            version	            string	    The (build) version the test was executed against

        If any custom fields are configured, they'll show up here too with the prefix custom_
        """
        command = 'get_results/{0}'.format(test_id)
        if limit is not None:
            command = self.add_argument(command, 'limit={0}'.format(limit))
        if offset is not None:
            command = self.add_argument(command, 'offset={0}'.format(offset))
        if status_id is not None:
            command = self.add_argument(command, 'status_id={0}'.format(','.join(str(x) for x in status_id)))
        try:
            response = self.send_get(command)
        except APIError as error:
            print(error)
        else:
            return response

    def get_results_for_case(self, run_id, case_id, limit=None, offset=None, status_id=None):
        """
        similar to get_results but it uses the case id instead of the test_id.  difference is, the test_id  is unique
        to a test run.  The case id is common across all runs that use that case.  For example: test suite A has a test
        case with id 55.  test run B is created and test case 55 is imported into that run.  The instance of case 55 is
        given a test id of 145.  get_results_for_case lets you use the case id of 55 to get results for this test.
        get_results would force you to use the test_id of 145 to get results for that test in that run.
        :type run_id: int
        :type case_id: int
        :type limit: int
        :type offset: int
        :type status_id: list
        :param run_id:
        :param case_id:
        :param limit: limit the number of reults to the first limit number of records.  if you want the first 20
                      then set limit=20
        :param offset: used to skip records.  if you want to skip the first 100 then send offset=100.
        :param status_id: list of integer status id'd you want to filter on.  the list is or'd so if you send [4,5]
                        you will get results with statuses of either 4 or 5 (retest, failed)
        :return:
        """
        command = 'get_results_for_case/{0}/{1}'.format(run_id, case_id)
        if limit is not None:
            command = self.add_argument(command, 'limit={0}'.format(limit))
        if offset is not None:
            command = self.add_argument(command, 'offset={0}'.format(offset))
        if status_id is not None:
            command = self.add_argument(command, 'status_id={0}'.format(','.join(str(x) for x in status_id)))
        try:
            response = self.send_get(command)
        except APIError as error:
            print(error)
        else:
            return response

    def get_results_for_run(self, run_id, created_after=None, created_before=None, created_by=None, limit=None,
                            offset=None, status_id=None):

        """

        :type run_id: int
        :type created_after: timestamp
        :type created_before: timestamp
        :type created_by: int
        :type limit: int
        :type offset: int
        :type status_id: int
        :param run_id:
        :param created_after:
        :param created_before:
        :param created_by:
        :param limit:
        :param offset:
        :param status_id:
        :return:
        """
        command = 'get_results_for_run/{0}'.format(run_id)
        # add optional args to command.  Only add one's whose value is not None (which is the default)
        if created_after is not None:
            command = self.add_argument(command, 'created_after={0}'.format(created_after))
        if created_before is not None:
            command = self.add_argument(command, 'created_before={0}'.format(created_before))
        if created_by is not None:
            command = self.add_argument(command, 'created_by={0}'.format(','.join(str(x) for x in created_by)))
        if limit is not None:
            command = self.add_argument(command, 'limit={0}'.format(limit))
        if offset is not None:
            command = self.add_argument(command, 'offset={0}'.format(offset))
        if status_id is not None:
            command = self.add_argument(command, 'status_id={0}'.format(','.join(str(x) for x in status_id)))

        try:
            response = self.send_get(command)
        except APIError as error:
            print(error)
        else:
            return response

    def add_result(self, test_id, status_id, comment=None, version=None, elapsed=None, defects=None,
                   assignedto_id=None, custom_fields_dict=None):
        """
        adds a result to a single test of a given id.  Use this if you only have one case to update.  If more
        than one, use add_results.
        :type test_id: int
        :type status_id: int
        :type comment: str
        :type version: str
        :type elapsed: str
        :type defects: list
        :type assignedto_id: int
        :type custom_fields_dict: dict
        :param test_id: required. integer test id of the test you want to update
        :param status_id: required. integer value for the test status you want to send.  see TestStatus class at
            the top for values.  e.g. For passed use self.test_status.PASSED.  for failed use self.test_status.FAILED.
        :param comment: optional. string comment/description for the test result
        :param version: optional. string version or build tested against
        :param elapsed: optional. string of how much time it took.  Use jira like times e.g. 30s for 30 seconds or
            2m 35s for 2 minutes and 35 seconds.  d for day, h for hour, m for minute and s for second.
        :param defects: optional. list of STRINGS indicating what defects have been logged against this case.
        :param assignedto_id: optional. the integer user id of the user this test should be assigned to.
        :param custom_fields_dict: optional. If your test has custom fields, here is where you pass values.  custom
            field names need to have the prefix custom_ in front of them for this to work.  For example: you have
            a custom string field called test_rack, to pass a value for that you would add a dict entry
            {custom_test_rack: 'value'}.  Append corresponding custom field elements to this dict for all custom
            fields you want to update on the test id in question.  Below are the custom field types supported:

            Name	            Type	    Description
            Checkbox	        bool	    True for checked and false otherwise
            Date	            string	    A date in the same format as configured for TestRail and API user
                                            (e.g. "07/08/2013")
            Dropdown	        int	        The ID of a dropdown value as configured in the field configuration
            Integer	            int	        A valid integer
            Milestone	        int	        The ID of a milestone for the custom field
            Multi-select	    array	    An array of IDs as configured in the field configuration
            Step Results	    array	    An array of objects specifying the step results. Also see the example below.
            String	            string	    A valid string with a maximum length of 250 characters
            Text	            string	    A string without a maximum length
            URL	                string	    A string with matches the syntax of a URL
            User	            int	        The ID of a user for the custom field

            Step Results Example (this is expanded for readability but its just a standard dict with a list of dicts
            for step results):
            {
                "status_id": 5,
                "comment": "This test failed",
                "elapsed": "15s",
                "defects": "TR-7",
                "version": "1.0 RC1 build 3724",

                ..

                "custom_step_results": [
                    {
                        "content": "Step 1",
                        "expected": "Expected Result 1",
                        "actual": "Actual Result 1",
                        "status_id": 1
                    },
                    {
                        "content": "Step 2",
                        "expected": "Expected Result 2",
                        "actual": "Actual Result 2",
                        "status_id": 2
                    },

                    ..
                ]

                ..
            }
        :return: same return type as get_results.  The only difference is it's a single dict result instead of a
                list of dict results.
        """

        # add required args
        result_data = {'status_id': status_id}
        # add optional args if they're !=None
        if comment is not None:
            result_data.update({'comment': comment})
        if version is not None:
            result_data.update({'version': version})
        if elapsed is not None:
            result_data.update({'elapsed': elapsed})
        if defects is not None:
            result_data.update({'defects': ','.join(str(x) for x in defects)})
        if assignedto_id is not None:
            result_data.update({'assignedto_id': assignedto_id})
        if custom_fields_dict is not None:
            result_data.update(custom_fields_dict)

        try:
            response = self.send_post('add_result/{0}'.format(test_id), result_data)
        except APIError as error:
            print(error)
        else:
            return response

    def add_test_results(self, run_id, list_of_result_dicts):
        """
        bulk add function.  Used to update multiple test cases in a run with one call.
        :type run_id: int
        :type list_of_result_dicts: list
        :param run_id: id of the run you want to update
        :param list_of_result_dicts: list of properly formatted result dict's.  Use result_builder to build the result
            dict's.
        :return:

        test_id example for list_of_result_dicts (expanded for readability):
        [
            {
                "test_id": 101,
                "status_id": 5,
                "comment": "This test failed",
                "defects": "TR-7"

            },
            {
                "test_id": 102,
                "status_id": 1,
                "comment": "This test passed",
                "elapsed": "5m",
                "version": "1.0 RC1"
            },

            ..

            {
                "test_id": 101,
                "assignedto_id": 5,
                "comment": "Assigned this test to Joe"
            }

            ..
        ]

        case_id example for list_of_result_dicts (expanded for readability:
        [
            {
                "case_id": 1,
                "status_id": 5,
                "comment": "This test failed",
                "defects": "TR-7"

            },
            {
                "case_id": 2,
                "status_id": 1,
                "comment": "This test passed",
                "elapsed": "5m",
                "version": "1.0 RC1"
            },

            ..

            {
                "case_id": 1,
                "assignedto_id": 5,
                "comment": "Assigned this test to Joe"
            }

            ..
        ]
        """
        if len(list_of_result_dicts) > 0:
            # determine whether case_id's or test_id's were used in the results.  There should be only one type.
            # raise exception if there are multiple types.  Tye type determines which bulk add results function to use
            # in testrail
            result_types = []
            for result in list_of_result_dicts:
                if 'test_id' in result:
                    result_types.append('test_id')
                elif 'case_id' in result:
                    result_types.append('case_id')
                else:
                    raise ValueError('Unknown case/test id key found or its missing.  Acceptable keys are test_id '
                                     'or case_id.  Result dict in question:\r\n{0}'.format(result))

            result_type = result_types[0]
            # check if all result types are the same.  converting a list to a set removes all duplicates so if the
            # length is 1 after the conversion then all items are the same.  If not, raise an exception.
            if len(set(result_types)) != 1:
                raise ValueError('Unexpected mismatch in test/case id keys.  they need to be the same for all test'
                                 'result dicts in the results list of dicts.  list of test/case id keys found: {0}'
                                 .format(result_types))
            else:
                result_data = {'results': list_of_result_dicts}
                try:
                    if result_type == 'test_id':
                        print('sending add_results')
                        response = self.send_post('add_results/{0}'.format(run_id), result_data)
                    elif result_type == 'case_id':
                        logging.debug('sending add_results_for_case \r\n {}'.format(result_data))
                        response = self.send_post('add_results_for_cases/{0}'.format(run_id), result_data)
                except APIError as error:
                    print(error)
                else:
                    return response
        else:
            raise ValueError("list_of_result_dicts is empty.  I require all the datas...resistance is futile")

    @staticmethod
    def result_builder(test_id, status_id, comment=None, version=None, elapsed=None, defects=None,
                       assignedto_id=None, custom_fields_dict=None, by_case=True):
        """
        builds a formatted result dict for a single result.  This is meant to be used with the bulk update functions
        add_results and add_results_by_case.  by_case is defaulted to True which means the passed in test id maps to
        the case_id from the suite and not the instanced test id in the test run.  So if you're using this with
        add_results then set by_case=False and pass in the test_id.  If you're using this with add_results_for_cases
        then leave by_case=True and pass in the case_id.
        NOTE: all referenced tests MUST belong to the same test run.
        :type test_id: int
        :type status_id: int
        :type comment: str
        :type version: str
        :type elapsed: str
        :type defects: list
        :type assignedto_id: int
        :type custom_fields_dict: dict
        :type by_case: bool
        :param test_id:
        :param status_id: required. integer value for the test status you want to send.  see TestStatus class at
            the top for values.  e.g. For passed use self.test_status.PASSED.  for failed use self.test_status.FAILED.
        :param comment: optional. string comment/description for the test result
        :param version: optional. string version or build tested against
        :param elapsed: optional. string of how much time it took.  Use jira like times e.g. 30s for 30 seconds or
            2m 35s for 2 minutes and 35 seconds.  d for day, h for hour, m for minute and s for second.
        :param defects: optional. list of STRINGS indicating what defects have been logged against this case.
        :param assignedto_id: optional. the integer user id of the user this test should be assigned to.
        :param custom_fields_dict: optional. If your test has custom fields, here is where you pass values.  See the
            custom_fields param description in add_result for more details.
        :param by_case: bool indicating whether you're using this with add_results or add_results_for_cases.
            If add_results, then set this to False and pass in the test_id for the test_id argument.  If you're using
            this with add_results_for_cases then leave this defaulted to False and pass in the case_id for the test_id
            argument.
        :return:

        """
        result_data = {}
        if by_case:
            result_data.update({'case_id': test_id})
        else:
            result_data.update({'test_id': test_id})

        result_data.update({'status_id': status_id})

        # add optional args if they're !=None
        if comment is not None:
            if isinstance(comment, str):
                result_data.update({'comment': comment})
            else:
                result_data.update({'comment': comment.decode('utf-8', errors='ignore')})
        if version is not None:
            if isinstance(version, str):
                result_data.update({'version': version})
            else:
                result_data.update({'version': version.decode('utf-8', errors='ignore')})
        if elapsed is not None:
            if isinstance(elapsed, str):
                result_data.update({'elapsed': elapsed})
            else:
                result_data.update({'elapsed': elapsed.decode('utf-8', errors='ignore')})
        if defects is not None:
            result_data.update({'defects': ','.join(str(x) for x in defects)})
        if assignedto_id is not None:
            result_data.update({'assignedto_id': assignedto_id})
        # if custom_fields_dict is not None:
        if custom_fields_dict:
            result_data.update(custom_fields_dict)

        return result_data

    def get_case(self, case_id):
        # type: (str or int) -> dict
        """
        gets test case details.
        :type case_id: int
        :param case_id: integer case id you want the details of.
        :return: dict with the following elements at a minimum:

            Name	            Type	    Description
            created_by	        int	        The ID of the user who created the test case
            created_on	        timestamp	The date/time when the test case was created (as UNIX timestamp)
            estimate	        timespan	The estimate, e.g. "30s" or "1m 45s"
            estimate_forecast	timespan	The estimate forecast, e.g. "30s" or "1m 45s"
            id	                int	        The unique ID of the test case
            milestone_id	    int	        The ID of the milestone that is linked to the test case
            priority_id	        int	        The ID of the priority that is linked to the test case
            refs	            string	    A comma-separated list of references/requirements
            section_id	        int	        The ID of the section the test case belongs to
            suite_id	        int	        The ID of the suite the test case belongs to
            template_id	        int	        The ID of the template (field layout) the test case
            title	            string	    The title of the test case
            type_id	            int	        The ID of the test case type that is linked to the test case
            updated_by	        int	        The ID of the user who last updated the test case
            updated_on	        timestamp	The date/time when the test case was last updated (as UNIX timestamp)
        """
        if self.help.check_arg_types("get_test", [[case_id, (str, int)]]):
            case_id_int = self.strip_id(case_id)
            try:
                response = self.send_get('get_case/{0}'.format(case_id_int))
            except APIError as error:
                print(error)
            else:
                return response

    def get_case_steps(self, case_id, list_of_case_dicts=None):
        # type: (str or int, List[dict]) -> List[Dict]
        """
        gets the existing test steps from a test case.  Used for updates to those steps later on.  In this case the
        custom field is custom_steps_executed.
        :param case_id:
        :return: list of step dictionaries.  example:
            [{u'content': u'Incandescent bulb', u'expected': u''},
            {u'content': u'Halogen bulb(no driver)', u'expected': u''},
            {u'content': u'Halogen MLV - Iron Core', u'expected': u''},
            {u'content': u'Halogen MLV - Torrodial', u'expected': u''},
            {u'content': u'Halogen ELV', u'expected': u''}]
        """
        if self.help.check_arg_types("get_case_steps", [[case_id, (str, int)], [list_of_case_dicts, (list, None)]]):
            case_id_int = self.strip_id(case_id)
            # if populated then search in list_of_case_dicts for the case.  If not, ping testrail for the case data
            if list_of_case_dicts:
                case_data = self.help.find_pair_in_list_of_dicts("case_id", case_id_int, list_of_case_dicts)
            else:
                case_data = self.get_case(case_id_int)
            if "custom_steps_separated" in case_data:
                test_steps = case_data["custom_steps_separated"]
                return test_steps
            else:
                raise ValueError("custom_steps_separated doesnt exist in case id: {}.  So test case step updates wont "
                                 "work downstream.".format(case_id))

    def get_cases(self, project_id, suite_id, section_id=None, limit=None, offset=None, title_filter=None,
                  created_after=None, created_before=None, created_by=None, milestone_id=None, priority_id=None,
                  template_id=None, type_id=None, updated_after=None, updated_before=None, updated_by=None):

        """
        gets data on multiple test cases in a list of dicts whose dict format is the same return as get_case.
        :type project_id: int
        :type suite_id: int
        :type section_id: int
        :type limit: int
        :type offset: int
        :type title_filter: str
        :type created_after: timestamp
        :type created_before: timestamp
        :type created_by: int
        :type milestone_id: list
        :type priority_id: list
        :type template_id: list
        :type type_id: list
        :type updated_after: timestamp
        :type updated_before: timestamp
        :type updated_by: int
        :param project_id: required.  id of the project
        :param suite_id: required.  id of the test suite
        :param section_id: optional.  integer id of the section in the suite you want to pull cases from.
        :param limit: optional.  limit the number of results to this number
        :param offset: optional.  max return is 250 records.  If there's more use this to grab the next set
        :param title_filter: optional. search filter for test case title.  returns records that contain the string.
        :param created_after: optional. unix timestamp.  returns records created after it
        :param created_before: optional. unix timestamp. returns records created before it
        :param created_by: optional. int user id the test cases were created by
        :param milestone_id: optional. list of integer milestone id's.  returns test cases that contain these milestone
            ids
        :param priority_id: optional. list of integer priority id's returns cases that contain these priority ids
        :param template_id: optional. list of integer template id's.  returns cases that contain these template ids
        :param type_id: optional. list of integer type id's.  returns cases that contain these type id's
        :param updated_after: optional. unix timestamp.  returns cases updated after this.
        :param updated_before: optional. unix timestamp.  returns cases updated before this.
        :param updated_by: optional. returns cases updated by this integer user id.
        :return: list of dict case results.  Dict's are in the same format as get_case.  see that function for details
        """

        command = 'get_cases/{0}&suite_id={1}'.format(project_id, suite_id)
        # add optional args to command.  Only add one's whose value is not None (which is the default)
        if section_id is not None:
            command = self.add_argument(command, 'section_id={0}'.format(section_id))
        if limit is not None:
            command = self.add_argument(command, 'limit={0}'.format(limit))
        if offset is not None:
            command = self.add_argument(command, 'offset={0}'.format(offset))
        if title_filter is not None:
            command = self.add_argument(command, 'filter={0}'.format(title_filter))
        if created_after is not None:
            command = self.add_argument(command, 'created_after={0}'.format(created_after))
        if created_before is not None:
            command = self.add_argument(command, 'created_before={0}'.format(created_before))
        if created_by is not None:
            command = self.add_argument(command, 'created_by={0}'.format(','.join(str(x) for x in created_by)))
        if milestone_id is not None:
            command = self.add_argument(command, 'milestone_id={0}'.format(','.join(str(x) for x in milestone_id)))
        if priority_id is not None:
            command = self.add_argument(command, 'priority_id={0}'.format(','.join(str(x) for x in priority_id)))
        if template_id is not None:
            command = self.add_argument(command, 'template_id={0}'.format(','.join(str(x) for x in template_id)))
        if type_id is not None:
            command = self.add_argument(command, 'type_id={0}'.format(','.join(str(x) for x in type_id)))
        if updated_after is not None:
            command = self.add_argument(command, 'updated_after={0}'.format(updated_after))
        if updated_before is not None:
            command = self.add_argument(command, 'updated_before={0}'.format(updated_before))
        if updated_by is not None:
            command = self.add_argument(command, 'updated_by={0}'.format(updated_by))

        try:
            response = self.send_get(command)
        except APIError as error:
            print(error)
        else:
            return response

    def add_case(self, section_id, title, template_id=None, type_id=None, priority_id=None, estimate=None,
                 milestone_id=None, refs=None, custom_fields_dict=None):
        """
        adds a test case to testrail.  required fields are section id and title.
        :type section_id: int
        :type title: str
        :type template_id: int
        :type type_id: int
        :type priority_id: int
        :type estimate: str
        :type milestone_id: int
        :type refs: str
        :type custom_fields_dict: dict
        :param section_id: required. integer id for the section you want the case added to.
        :param title: required. utf-8 string of the title for the test case.
        :param template_id: optional. The ID of the template (field layout) you want to use.
        :param type_id: optional. integer id of the case type.
        :param priority_id: optional. integer id of the priority.
        :param estimate: optional. string timespan of how long the test is estimated to take.  h for hours
            , m for minutes, s for sections.  1:30:45 would be sent as 1h 30m 45s
        :param milestone_id: optional. integer id of the milestone to link to the test case
        :param refs: optional. string comma seperated list of references/requirements
        :param custom_fields_dict: optional. If your test has custom fields, here is where you pass values.  custom
            field names need to have the prefix custom_ in front of them for this to work.  For example: you have
            a custom string field called test_rack, to pass a value for that you would add a dict entry
            {custom_test_rack: 'value'}.  Append corresponding custom field elements to this dict for all custom
            fields you want to update on the test id in question.  Below are the custom field types supported:

            Name	            Type	    Description
            Checkbox	        bool	    True for checked and false otherwise
            Date	            string	    A date in the same format as configured for TestRail and API user
                                            (e.g. "07/08/2013")
            Dropdown	        int	        The ID of a dropdown value as configured in the field configuration
            Integer	            int	        A valid integer
            Milestone	        int	        The ID of a milestone for the custom field
            Multi-select	    array	    An array of IDs as configured in the field configuration
            Step Results	    array	    An array of objects specifying the step results. Also see the example below.
            String	            string	    A valid string with a maximum length of 250 characters
            Text	            string	    A string without a maximum length
            URL	                string	    A string with matches the syntax of a URL
            User	            int	        The ID of a user for the custom field
        :return: same response type as get_case but for the case you added.  see that function for details.
        """
        # add required args first
        case_data = {'title': self.strip_bad_data(title)}
        # add optional args to run_data.  Only add one's whose value is not None (which is the default)
        if template_id is not None:
            case_data.update({'template_id': template_id})
        if type_id is not None:
            case_data.update({'type_id': type_id})
        if priority_id is not None:
            case_data.update({'priority_id': priority_id})
        if estimate is not None:
            case_data.update({'estimate': self.strip_bad_data(estimate)})
        if milestone_id is not None:
            case_data.update({'milestone_id': milestone_id})
        if refs is not None:
            case_data.update({'refs': self.strip_bad_data(refs)})
        if custom_fields_dict is not None:
            case_data.update(custom_fields_dict)

        try:
            response = self.send_post('add_case/{0}'.format(section_id), case_data)
        except APIError as error:
            print(error)
        else:
            return response

    def update_case_TODO(self, case_id):
        pass

    def delete_case_TODO(self, case_id):
        pass

    @property
    def get_case_types(self):
        """
        returns a list of dicts where each dict containing all available case types.
        :return: list of dicts with case types.  Example:
            [
                {
                    "id": 1,
                    "is_default": false,
                    "name": "Automated"
                },
                {
                    "id": 2,
                    "is_default": false,
                    "name": "Functionality"
                },
                {
                    "id": 6,
                    "is_default": true,
                    "name": "Other"
                },
                ..
            ]
        """
        try:
            response = self.send_get('get_case_types')
        except APIError as error:
            print(error)
        else:
            return response

    def find_case_in_section(self, project_id, suite_id, section_id, testcase_name):
        """
        looks for a testcase in the provided section of the suite in the project with the same name as testcase_name
        If it finds it then it returns a get_case response dict for that case.  If not it returns None
        :type project_id: int
        :type suite_id: int
        :type section_id: int
        :type testcase_name: str
        :param project_id: required. integer project id
        :param suite_id: required. integer suite id
        :param section_id: required. integer section id for the section in the suite containing the case you're
            looking for.
        :param testcase_name: required. string name of the testcase you're looking for.
        :return: None if it doesnt find a case.  a get_case response dict if it does
        """
        cases = self.get_cases(project_id, suite_id, section_id=section_id)
        matching_cases = []
        if len(cases) == 0:
            # no cases found in that section id.  return None
            return None
        else:
            # iterate through the found cases in that section and see if we have a match.
            for case in cases:
                if case['title'] == testcase_name:
                    matching_cases.append(case)
        if len(matching_cases) == 0:
            return None
        elif len(matching_cases) == 1:
            return matching_cases[0]
        else:
            raise ValueError('Found more than one test case with testcase name: {0}.  In section_id: {1} of '
                             'suite {2} in project {3}.  Testcase names have to be unique in the same nested'
                             'section.'.format(testcase_name, section_id, suite_id, project_id))

    def get_case_ids_by_custom_tag(self, suite_id, tag_ids, project_id=27):
        """

        :type project_id: int
        :type suite_id: int
        :type tag_ids: list
        :param project_id:
        :param suite_id:
        :param tag_ids:
        :return:
        """
        cases_list = []
        cases = self.get_cases(project_id, suite_id)
        print(len(cases))
        for case in cases:
            if any(elem in case['custom_tags'] for elem in tag_ids):
                cases_list.append(case['id'])
        # convert to a set to remove any possible duplicates, then convert back to a list for return.
        return list(set(cases_list))

    # Sections api
    def get_section(self, section_id):

        """
        gets details for a particular section or subsection of a suite in testrail.
        :type section_id: int
        :param section_id: required. integer id of the section you want.
        :return: dict with the following entries:
            Name	            Type	    Description
            -------------------------------------------------------------------------------------------------------
            depth               int         The level in the section hierarchy of the test suite
            description         string      The description of the section
            display_order       int         The order in the test suite
            id                  int         The unique id of the section
            parent_id           int         The ID fo the parent section in the test suite
            name                string      The name of the section
            suite_id            int         the ID of the test suite this section belongs to.
        """
        try:
            response = self.send_get('get_section/{0}'.format(section_id))
        except APIError as error:
            print(error)
        else:
            return response

    def get_sections(self, project_id, suite_id):
        """
        returns a list of get_section responses for each section in a suite.
        :type project_id: int
        :type suite_id: int
        :param project_id:
        :param suite_id:
        :return: list of get_section dict's for each section in the suite
        """
        try:
            response = self.send_get('get_sections/{0}&suite_id={1}'.format(project_id, suite_id))
        except APIError as error:
            print(error)
        else:
            return response

    def add_section(self, project_id, suite_id, name, parent_id=None, description=None):
        """
        adds a section to a test suite.  Supports nested sections if parent_id is passed in.
        :type project_id: int
        :type suite_id: int
        :type name: str
        :type parent_id: int
        :type description: str
        :param project_id:
        :param suite_id:
        :param name:
        :param parent_id:
        :param description:
        :return:
        """
        # add required args first
        section_data = {
            'name': self.strip_bad_data(name)
            , 'suite_id': suite_id
        }
        # add optional args to section_data.  Only add one's whose value is not None (which is the default)
        if parent_id is not None:
            section_data.update({'parent_id': parent_id})
        if description is not None:
            section_data.update({'description': self.strip_bad_data(description)})

        try:
            print('project_id: {0}.  section_data: {1}'.format(project_id, section_data))
            response = self.send_post('add_section/{0}'.format(project_id), section_data)
            print(response)
        except APIError as error:
            print(error)
        else:
            return response

    def add_nested_sections(self, project_id, suite_id, section_name_list):
        # type: (int, int, List[str]) -> int
        """
        Adds nested sections to a test suite if they don't already exist.  If they do, it does nothing.  This returns
        an integer id of the last nested section id in the chain.For example: section_name_list = [first, second
        , third]: if root section (no parent id) named "first" doesnt exist then it adds it.  If a section
        named "second" with a parent section named "first" doesnt exist then it adds it.  If a section named
        "third" with a parent section named "second" that has a parent section named "first" doesnt exist then
        it adds it.  the function would return the integer id of the section named "third" in this example.
        :param project_id: required. integer ID for the project you're working with.
        :param suite_id: required. integer ID for the suite within project_id you're working with.
        :param section_name_list: list of string section names that you want to add if they dont exist
        :return: integer id for the last section in section_name_list
        """
        current_sections = self.get_sections(project_id, suite_id)
        current_parent = None
        for depth, section_name in enumerate(section_name_list):
            # depth is the index of the section name in section_name_list
            matching_section = self.find_matching_section(current_sections, section_name, current_parent, depth)
            if len(matching_section) > 0:
                # section found, set current parent to this sections id.
                current_parent = matching_section['id']
            else:
                # section not found, add it
                # print('section name: {0} with parent: {1} at depth: {2} not found.  Adding it'
                #     .format(section_name, current_parent, depth))
                response = self.add_section(project_id, suite_id, section_name, current_parent)
                current_parent = response['id']
                # append the add response to current_sections so we dont have to get that again
                current_sections.append(response)
        return current_parent

    def update_section(self, section_id, name=None, description=None):
        # type: (int, str, str) -> Dict
        """
        function to update a section in testrail.
        :param section_id: required. integer ID for the section you want to update.
        :param name: optional. change the string section name to this.
        :param description: optional. change the string description of the section to this.
        :return: dict in the same return format as get_section.  see that function for details/
        """
        section_data = {}
        # add optional args to section_data.  Only add one's whose value is not None (which is the default)
        if name is not None:
            section_data.update({'name': self.strip_bad_data(name)})
        if description is not None:
            section_data.update({'description': self.strip_bad_data(description)})

        if len(section_data) > 0:
            try:
                response = self.send_post('update_section/{0}'.format(section_id), section_data)
            except APIError as error:
                print(error)
            else:
                return response
        else:
            raise ValueError('name and/or description args to update_section werent passed in.  1 or both have to '
                             'be populated in order to update a section.  I got Name={0}, description={1}'
                             .format(name, description))

    def delete_section(self, section_id):
        # type: (int) -> str
        """
        deletes a section in testrail.  Please note: Deleting a section cannot be undone and also deletes all
        related test cases as well as active tests & results, i.e. tests & results that weren't closed (archived)
        yet.  So don't do this unless you're absolutely sure.
        :type section_id: int
        :param section_id: reqeuired. integer ID for the section you want to delete.
        :return:
        """
        try:
            response = self.send_post('delete_section/{0}'.format(section_id), None)
        except APIError as error:
            print(error)
        else:
            return response

    @staticmethod
    def find_matching_section(sections_list, name, parent_id, depth):
        list_of_match_dicts = []
        for i, section in enumerate(sections_list):
            if section['name'] == name and section['parent_id'] == parent_id and section['depth'] == depth:
                list_of_match_dicts.append(section)
        # print('matches: {0}'.format(matches))
        if len(list_of_match_dicts) == 0:
            return {}
        elif len(list_of_match_dicts) == 1:
            return list_of_match_dicts[0]
        else:
            raise ValueError('Found more than 1 section with the same name, parent_id and depth.  Fix the test suite '
                             'so there is only ever one section name with the same parent id and depth.  i got '
                             'name: {0}, parent_id: {1}, depth: {2}'.format(name, parent_id, depth))

    @staticmethod
    def strip_id(testrail_id):
        # type: (str or int) -> int
        """
        Strips off the first letter character of an id.  The testrail ui puts a letter in front of the id's visible to
        users on their web page.  Like all Run id's start with R, all suites start with S etc.  But the api doesnt use
        it.  So this strips it off if its there.
        :type testrail_id: str or int
        :param testrail_id: string of the id to check
        :return: int id with any letter designator at the beginning stripped off.
        """
        if isinstance(testrail_id, str):
            if testrail_id[:1].isalpha():
                stripped_id = int(testrail_id[1:])
            else:
                stripped_id = int(testrail_id)
            return stripped_id
        elif isinstance(testrail_id, int):
            return testrail_id

    @staticmethod
    def strip_bad_data(data):
        # this is not needed in python3 since strings in python3 do this natively and there is no longer a decode
        # function for strings.  So for python3 we just return the data back.  Ill leave the function calls in place
        # in case we identify a need to strip off bad data later on.

        # return data.decode('utf-8', errors='ignore')

        return data

    def get_plan(self, plan_id):
        # type: (int) -> Dict
        """
        Gets data from the test plan.
        :param plan_id: Required. integer ID of the test plan you want data for.
        :return: Dict with the following possible elements.  Example below that.

                Name	            Type	    Description
            -------------------------------------------------------------------------------------------------------
            assignedto_id           int	        The ID of the user the entire test plan is assigned to
            blocked_count	        int	        The amount of tests in the test plan marked as blocked
            completed_on	        timestamp	The date/time when the test plan was closed (as UNIX timestamp)
            created_by	            int	        The ID of the user who created the test plan
            created_on	            timestamp	The date/time when the test plan was created (as UNIX timestamp)
            custom_status_count	    int	        The amount of tests in the test plan with the respective custom status
            description	            string	    The description of the test plan
            entries	                array	    An array of 'entries', i.e. group of test runs
            failed_count	        int	        The amount of tests in the test plan marked as failed
            id	                    int	        The unique ID of the test plan
            is_completed	        bool	    True if the test plan was closed and false otherwise
            milestone_id	        int	        The ID of the milestone this test plan belongs to
            name	                string	    The name of the test plan
            passed_count	        int	        The amount of tests in the test plan marked as passed
            project_id	            int	        The ID of the project this test plan belongs to
            retest_count	        int	        The amount of tests in the test plan marked as retest
            untested_count	        int	        The amount of tests in the test plan marked as untested
            url	                    string      The address/URL of the test plan in the user interface

        Example response:
        {
            "assignedto_id": null,
            "blocked_count": 2,
            "completed_on": null,
            "created_by": 1,
            "created_on": 1393845644,
            "custom_status1_count": 0,
            "custom_status2_count": 0,
            "custom_status3_count": 0,
            "custom_status4_count": 0,
            "custom_status5_count": 0,
            "custom_status6_count": 0,
            "custom_status7_count": 0,
            "description": null,
            "entries": [
            {
                "id": "3933d74b-4282-4c1f-be62-a641ab427063",
                "name": "File Formats",
                "runs": [
                {
                    "assignedto_id": 6,
                    "blocked_count": 0,
                    "completed_on": null,
                    "config": "Firefox, Ubuntu 12",
                    "config_ids": [
                        2,
                        6
                    ],
                    "custom_status1_count": 0,
                    "custom_status2_count": 0,
                    "custom_status3_count": 0,
                    "custom_status4_count": 0,
                    "custom_status5_count": 0,
                    "custom_status6_count": 0,
                    "custom_status7_count": 0,
                    "description": null,
                    "entry_id": "3933d74b-4282-4c1f-be62-a641ab427063",
                    "entry_index": 1,
                    "failed_count": 2,
                    "id": 81,
                    "include_all": false,
                    "is_completed": false,
                    "milestone_id": 7,
                    "name": "File Formats",
                    "passed_count": 2,
                    "plan_id": 80,
                    "project_id": 1,
                    "retest_count": 1,
                    "suite_id": 4,
                    "untested_count": 3,
                    "url": "http://<server>/testrail/index.php?/runs/view/81"
                },
                {
                    ..
                }
                ],
                "suite_id": 4
            }
            ],
            "failed_count": 2,
            "id": 80,
            "is_completed": false,
            "milestone_id": 7,
            "name": "System test",
            "passed_count": 5,
            "project_id": 1,
            "retest_count": 1,
            "untested_count": 6,
            "url": "http://<server>/testrail/index.php?/plans/view/80"
        }

        """
        if self.help.check_arg_types('get_plan', [[plan_id, (str, int)]]):
            plan_id_int = self.strip_id(plan_id)
            try:
                response = self.send_get('get_plan/{0}'.format(plan_id_int))
            except APIError as error:
                print(error)
            else:
                return response

    def get_plans(self, project_id):
        # type: (int) -> List[Dict]
        """
        returns get_plan data for every test plan in a given project.
        :param project_id: Required. integer ID for the project you want plans data from
        :return: list of get_plan response dictionaries.  See the get_plan method's return data for details.
        """
        if self.help.check_arg_types('get_plans', [[project_id, int]]):
            try:
                response = self.send_get('get_plans/{0}'.format(project_id))
            except APIError as error:
                print(error)
            else:
                return response

    def add_plan(self, name  # type: str
                 , description  # type: str
                 , project_id  # type: int
                 , list_of_entry_dicts  # type: List[Dict]
                 , milestone_id=0  # type: int
                 ):
        # type: (...) -> Dict
        """
        adds a test plan for a given project.  If you populate list_of_entry_dicts it adds test runs to the plan during
        plan creation.  If you don't, you can use add_plan_entry after its created.
        :param name: required.  string name of the test plan.
        :param description: required.  string description of the test plan
        :param project_id: required.  integer ID of the project you want to add the plan to.
        :param list_of_entry_dicts: use the plan_entry_builder method to create entry dictionaries.  Append them to a
            list and pass them in here.
        :param milestone_id: optional.  The integer ID of the milestone to link to the test plan
        :return: dict with header level info on the new plan created as well as get_run type data for any test
            run created using list_of_entry_dicts.  return type is the same as get_plan.  see that for details.
        """
        if self.help.check_arg_types('add_plan', [[name, str], [description, str], [project_id, int]
            , [list_of_entry_dicts, list], [milestone_id, int]]):
            # add required args first
            plan_data = {
                'name': name
                , 'description': description
                , 'entries': list_of_entry_dicts
            }
            # add optional args to plan_data.
            if milestone_id:
                plan_data.update({'milestone_id': milestone_id})

            try:
                response = self.send_post('add_plan/{0}'.format(project_id), plan_data)
            except APIError as error:
                print(error)
            else:
                return response

    def add_plan_entry(self, plan_id, plan_entry_dict):
        # type: (int, Dict) -> Dict
        """
        Adds an entry to an existing test plan.
        :param plan_id: Required. formatted plan entry dictionary.  use the plan_entry_builder method to make one.
        :param plan_entry_dict: Required. formatted plan entry dictionary.  use the plan_entry_builder method to make one.
        :return: If successful, this method returns the new test plan entry including test runs using the same response
            format as the entries field of get_plan, but for a single entry instead of a list of entries.

        """
        if self.help.check_arg_types('add_plan_entry', [[plan_id, int], [plan_entry_dict, dict]]):
            try:
                response = self.send_post('add_plan/{0}'.format(plan_id), plan_entry_dict)
            except APIError as error:
                print(error)
            else:
                return response

    def plan_entry_builder(self, suite_id  # type: int
                           , name  # type: str
                           , description  # type: str
                           , assignedto_id=0  # type: int
                           , case_ids=None  # type: List[int]
                           , config_ids=None  # type: List[int]
                           , runs_list_of_dicts=None  # type: List[Dict]
                           ):
        # type: (...) -> Dict
        """
        Formats a plan entry dictionary.  This can be consumed by add_plan_entry directly or appended to a list and
            consumed by add_plan.
        :param plan_id: Required. Integer ID of the plan you want to add an entry to.
        :param suite_id: Required. The integer ID of the test suite for the test run(s).
        :param name: Required. The string name of the plan entry you want to add.  If runs_list_of_dicts is populated
            you can override this default name for individual run entries there.
        :param description: Required. The string description of the test run entries being added to the test plan
        :param assignedto_id: Optional. integer ID of the user you want this entry(ies) assigned to.  Can be
            overridden in the runs_list_of_dicts if you use it.
        :param case_ids: Optional. list of integer case IDs for cases you want added in this plan entry.  If omitted
            it adds all cases from the suite.  Can be overridden if you're using the runs_list_of_dicts.
        :param config_ids: Optional: A list of integer configuration IDs used for the test runs of the test plan entry.
        :param runs_list_of_dicts: Optional. A list of dicts of test runs with configurations.  Use the
            entry_run_builder method to create the individual run dictionaries you want.  Then append them to a list
            and pass that list in here.  Please see the example below for details.
        :return: Properly formatted plan entry dictionary ready to be consumed by add_plan_entry directly or appended
            to a list and consumed by add_plan.

        Example which shows how to create a new test plan entry with multiple test runs and configurations:
        {
            "suite_id": 1,
            "assignedto_id": 1,           // Default assignee
            "include_all": true,          // Default selection
            "config_ids": [1, 2, 4, 5, 6],
            "runs": [
                {
                    "include_all": false, // Override selection
                    "case_ids": [1, 2, 3],
                    "config_ids": [2, 5]
                },
                {
                    "include_all": false, // Override selection
                    "case_ids": [1, 2, 3, 5, 8],
                    "assignedto_id": 2,   // Override assignee
                    "config_ids": [2, 6]
                }

                ..
            ]
        }
        """
        if runs_list_of_dicts is None:
            runs_list_of_dicts = []
        if config_ids is None:
            config_ids = []
        if case_ids is None:
            case_ids = []
        if self.help.check_arg_types('plan_entry_builder', [[suite_id, int], [name, str], [description, str]
            , [assignedto_id, int], [case_ids, list], [config_ids, list]
            , [runs_list_of_dicts, list]]):
            # add required args first
            entry_data = {
                'suite_id': suite_id
                , 'name': name
                , 'description': description
            }
            # add optional args to plan_data.
            if assignedto_id:
                entry_data.update({'assignedto_id': assignedto_id})
            if case_ids:
                entry_data.update({'case_ids': case_ids})
                entry_data.update({'include_all': False})
            else:
                entry_data.update({'include_all': True})
            if config_ids:
                entry_data.update({'config_ids': config_ids})
            if runs_list_of_dicts:
                entry_data.update({'runs': runs_list_of_dicts})

            return entry_data

    def entry_run_builder(self, case_ids  # type: List[int]
                          , name=""  # type: str
                          , description=""  # type: str
                          , assignedto_id=0  # type: int
                          , config_ids=None  # type: List[int]
                          ):
        # type: (...) -> Dict
        """
        builds the optional "runs" element of a plan entry. Each of these args overwrite the values passed in to the
            parent entry.  A regular element is sufficient for everything my team needs.  I added this incase someone
            else needs it.  See documentation below.
        :param case_ids: Required. list of integer case ids that you want included in the entries run you're creating
        :param name: Optional. string name of the entries run you're creating.
        :param description: Optional. string description of the entries run you are creating.
        :param assignedto_id: Optional. Integer id of the user you want the entry run assigned to.
        :param config_ids: Optional. List of integer config id's you want this entry run to use.
        :return:

        {
            "suite_id": 1,
            "assignedto_id": 1,           // Default assignee
            "include_all": true,          // Default selection
            "config_ids": [1, 2, 4, 5, 6],
            "runs": [
                {
                    "include_all": false, // Override selection
                    "case_ids": [1, 2, 3],
                    "config_ids": [2, 5]
                },
                {
                    "include_all": false, // Override selection
                    "case_ids": [1, 2, 3, 5, 8],
                    "assignedto_id": 2,   // Override assignee
                    "config_ids": [2, 6]
                }

                ..
            ]
        }

        This will effectively create a new test run for each array element of the runs field. The top-level
        assignedto_id, include_all and case_ids fields specify the default assignee and test case selection for all
        test runs. You can override these fields for each test run as demonstrated in the example above.

        The top-level config_ids field specifies the combined list of configurations for the list of test runs.
        All configurations referenced by the individual test runs must be included in this field. Each test run can
        specify one configuration per included configuration group and needs to match a full configuration
        combination. For example, let's assume we have the following configurations and configuration groups:

        ID	Group	Configuration
        1	Browsers	Chrome
        2	Browsers	Firefox
        3	Browsers	Internet Explorer
        4	Operating Systems	Windows 7
        5	Operating Systems	Windows 8
        6	Operating Systems	Ubuntu 12
        The top-level config_ids field from the example includes the configurations 1, 2, 4, 5 and 6. Valid
        configuration combinations need to include one configuration from each configuration group. Valid
        combinations are therefore:

        ID	Combination
        1,4	Chrome, Windows 7
        1,5	Chrome, Windows 8
        1,6	Chrome, Ubuntu 12
        2,4	Firefox, Windows 7
        2,5	Firefox, Windows 8
        2,6	Firefox, Ubuntu 12
        The example chooses to include only two of these combinations, namely 2,5 (Firefox, Windows 8) and 2,6
        (Firefox, Ubuntu 12). TestRail in turn will add two separate test runs, one for each combination.
        """
        if config_ids is None:
            config_ids = []
        if self.help.check_arg_types('entry_run_builder', [[case_ids, list], [name, str], [description, str]
            , [assignedto_id, int], [config_ids, list]]):
            run_dict = {
                "case_ids": case_ids,
                "include_all": False
            }
            # add optional args to plan_data.
            if name:
                run_dict.update({'name': name})
            if description:
                run_dict.update({'description': description})
            if assignedto_id:
                run_dict.update({'assignedto_id': assignedto_id})
            if config_ids:
                run_dict.update({'config_ids': config_ids})

            return run_dict

    def get_name_from_suite(self, suite_id):
        # type: (int) -> str
        self.help.check_arg_types('get_name_from_suite', [[suite_id, int]])
        suite_data = self.get_suite(suite_id)
        name = suite_data['name']
        return name

    def placeholder(self):
        # pycharm keeps hosing indenting if you add a function at the bottom.  If i add them above this it works
        # fine.  That's the only function for this.
        pass


if __name__ == '__main__':
    pyt = PyTestRail('bzuck@control4.com', 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.')

    # print(pyt.get_plan(4032))
    print(pyt.is_case_in_run(1263027, 5473))
    print(pyt.get_runid_for_case_in_plan(1263027, 5472))

    # plan_entries = []
    # entry1 = pyt.plan_entry_builder(2552, 'programatically added run 1', 'programatically added run 1 description')
    # entry2 = pyt.plan_entry_builder(2684, 'programatically added run 2', 'programatically added run 2 description')
    # entry3 = pyt.plan_entry_builder(2684, 'programatically added run 3', 'programatically added run 3 description')
    #
    # plan_entries.append(entry1)
    # plan_entries.append(entry2)
    # plan_entries.append(entry3)
    #
    # response = pyt.add_plan('programatically added test plan 1', 'programatically added plan 1 description', 27, plan_entries)
    #
    # print(response)

    # print(pyt.send_get('get_projects'))
    # print(pyt.get_project(27))
    # suites = pyt.get_suites(27)
    # print(pyt.get_suite(2552))
    # print(pyt.get_project_id('Embedded Systems'))
    # print(pyt.get_suite_id(pyt.get_project_id('Embedded Systems'), 'add_suite_test1'))
    # print(pyt.add_suite(pyt.get_project_id('Embedded Systems'), "add_suite_test1", "used the api to add this suite.  first attempt"))
    # print(pyt.update_suite(pyt.get_suite_id(pyt.get_project_id('Embedded Systems'), 'add_suite_testupdated3')
    #                        , description='updated description 2'))
    # print(pyt.get_suite_id(pyt.get_project_id('Embedded Systems'), 'add_suite_testupdated3'))

    # test_runs = pyt.get_runs(pyt.get_project_id('Embedded Systems'))
    # for run in test_runs:
    #     # print(run)
    #     print('run_id: {0}, name: {1}, suite_id: {2}, is_completed: {3}, passed_count: {4}'
    #           .format(run['id'], run['name'], run['suite_id'], run['is_completed'], run['passed_count']))
    # print(pyt.get_run(2866))
    # print(pyt.add_run(27, 2552, 'API test run creation test 1', 'API test only.  test run creation test 1'))
    # response from above is: {u'include_all': True, u'is_completed': False, u'custom_status3_count': 0, u'created_on': 1569279849, u'retest_count': 0, u'id': 3045, u'plan_id': None, u'created_by': 45, u'passed_count': 0, u'project_id': 27, u'config': None, u'custom_status6_count': 0, u'failed_count': 0, u'description': u'API test only.  test run creation test 1', u'custom_status5_count': 0, u'suite_id': 2552, u'milestone_id': None, u'name': u'API test run creation test 1', u'assignedto_id': None, u'blocked_count': 0, u'completed_on': None, u'config_ids': [], u'url': u'https://testrail.control4.com/index.php?/runs/view/3045', u'custom_status4_count': 0, u'untested_count': 7, u'custom_status2_count': 0, u'custom_status1_count': 0, u'custom_status7_count': 0}
    # print(pyt.update_run(3045
    #                      , name='API test run creation test 3'
    #                      , description='API test only.  switched include all to false and specified 4 cases to remain'
    #                      , include_all_cases=False
    #                      , case_ids=[1396151, 1396149, 1396146, 1396148]))
    # print(pyt.get_results(1372756))
    # print(pyt.get_results_for_case(2826, 927617))

    # run_results = pyt.get_results_for_run(2826)
    # # print(run_results)
    # for result in run_results:
    #     if result['test_id'] == 1370221:
    #         print(result)

    # print(pyt.add_result(1396412, pyt.test_status.PASSED
    #                      , comment='api_update to PASSED'
    #                      , version='FW version under test'
    #                      , elapsed='1m 20s'
    #                      # , defects=['ES-2536', 'ES-2537']
    #                      ))
    # print(pyt.get_case_types)

    # response = pyt.get_case(702912)
    # response = pyt.get_case(1043207)

    # response = pyt.get_case(1261568)
    # print(response)

    # custom_tcstatus: 1
    # custom_automation_status: 4
    # print(pyt.get_sections(27, 2599))
    # print(type(response['custom_tags']))
    # print(pyt.get_case(1034075))
    # print(pyt.get_case(1034076))
    # print(pyt.get_case(1034073))

    # print(pyt.send_get('get_case_fields'))

    # response = pyt.get_case_ids_by_custom_tag(27, 1783, [38, 4])
    # print(len(response))

    # custom_fields_dict = {
    #     'custom_tcstatus': 1
    #     , 'custom_automation_status': 4
    # }
    # last_section_id = 148052
    # testcase_name = 'test add case with required fields 1'
    # response = pyt.add_case(last_section_id, testcase_name, custom_fields_dict=custom_fields_dict)
