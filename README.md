<h1>Using Testrail Run Generator</h1>

<h3>This project creates a testrail run and includes all or specified test cases</h3>

<h4>arguments that require parameters</h4>
--project_id <br>
--suite_id <br>
--testrun_name <br>
--include_all_cases <br>
--list <br>

Example of a test run with all test cases in a test suite <br>
```python __main__.py --project_id 59 --suite_id 23407 --testrun_name BDD:API_Test --include_all_cases True```

Example of a test run with specific test cases <br>
```python __main__.py --project_id 59 --suite_id 23407 --testrun_name BDD:API_Test --include_all_cases False --list 3871665 3878729```