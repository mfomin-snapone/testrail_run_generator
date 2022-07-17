import logging
from typing import List

logger = logging.getLogger(__name__)


class Helpers():
    # This class is for helper functions etc that are commonly used in the various LaW_Test_Automation projects.
    def __init__(self):
        # add stuff here if it needs to be different for each instanciation of the class
        pass

    @staticmethod
    def check_arg_types(function_name,    # type: str
                        arguments_and_types     # type: List[List]
                        ):
        """
        This checks the type for arguments in a function.  If there are type mismatches in the arguments provided,
        a list of errors are generated that identify the function they reside in, the position of the argument in
        the argument list and what's wrong with it.  The errors are raised in an exception.  If no errors the function
        returns True so you can use this check in an if statement.
        :type function_name: str
        :type arguments_and_types: [[]]
        :param function_name: name of function who's arguments are being type checked
        :param arguments_and_types: list of argument and type lists.
                                    [[arg1, arg1_type], [arg2, arg2_type], [arg3, arg3_type], ... ]
        :return: Boolean True if all arg's are correctly typed.  If not, a ValueError exception is raised
        """
        errors = []
        position = 0
        for arg_and_type in arguments_and_types:
            position += 1
            arg = arg_and_type[0]
            typ = arg_and_type[1]
            if type(typ) == tuple:
                if None in typ:
                    # handle None being passed in as a type in a tuple.  convert to list, replace None with type(None)
                    # and convert back to a tuple
                    typ_list = list(typ)
                    typ_list = [type(None) if v is None else v for v in typ_list]
                    typ = tuple(typ_list)
            if typ == None:
                typ = type(None)
            if not isinstance(arg, typ):
                current_error = "check_args: {0} type check failed for argument {1} in function: {2}, received: {3} " \
                                "which isn't of type {0}".format(typ.__name__, position, function_name, arg)
                errors.append(current_error)
        if len(errors) > 0:
            raise ValueError(errors)
        else:
            return True

    @staticmethod
    def list_to_comma_delim_string(list_to_convert):
        """
        simple function to convert a list into a comma delimited string
        :rtype: str
        :type list_to_convert: list
        :param list_to_convert: list you want converted to a comma delimited string
        :return: string of the list converted to comma delimited.
        """
        if isinstance(list_to_convert, list):
            return ', '.join(map(str, list_to_convert))

    @staticmethod
    def find_in_str_list(find_val, in_list):
        # type: (str, List[str]) -> int
        """
        iterates through in_list looking for a list index whose find_val exists in a value in in_list.  example:
            in_list = ["stuff", "stuff/things/bears", "stuff/things"]
            find_val = "bears"
            this will return an index of 1 since that index's string contains the value in find_val.
            if find_val isnt found in any of in_list's indexes then it returns -1
        :param find_val: string value you're looking for
        :param in_list: list of strings
        :return: integer index.  if not found it returns -1
        """
        for idx in range(0, len(in_list)):
            if in_list[idx].__contains__(find_val):
                print("found at index {}.  val: {}".format(idx, in_list[idx]))
                return idx
        return -1

    @staticmethod
    def find_pair_in_list_of_dicts(key                  # type: str
                                   , value
                                   , list_of_dicts      # type: List[dict]
                                   , return_index=False # type: bool
                                   ):
        # type: (...) -> None or int or dict
        """
        Searches a list of dictionaries for a key value pair.  If it finds it then it either returns the dictionary
        containing it or the index in the list of that dictionary.  If return_index is false then it returns the dict.
        If return_index is true then it returns the integer index of the dictionary in the list.
        :param key: string key to look for.
        :param value: value associated with the key to look for.
        :param list_of_dicts: List of dictionaries to search in
        :param return_index: bool.  True if you want the index returned, False if you want the found dictionary returned.
        :return: None or the integer index found or the dictonary found.
        """
        found_index = next((index for (index, d) in enumerate(list_of_dicts) if d[key] == value), None)
        if found_index >= 0:
            if return_index:
                return found_index
            else:
                return list_of_dicts[found_index]
        else:
            raise ValueError("Didnt find key: {0}, value: {1} in the list of dictionaries: \r\n{2}"
                             .format(key, value, list_of_dicts))

    @staticmethod
    def replace_in_string_template(dict_with_template_replacements, string_template):
        """
        This function takes a dict with values to be searched for and replaced in the provided string_template. The
            values searched for are in an xml like format #tag!#.
        :type string_template: str
        :type dict_with_template_replacements: dict
        :param dict_with_template_replacements: dictionary with string replacements to be done on the string_template
            passed in.
        :param string_template: String template with tags to be searched for and replaced.
        :return: string template with the tags found and replaced.
        """
        if Helpers.check_arg_types('build_c4soap_cmd', [[dict_with_template_replacements, dict], [string_template, str]]):
            result = string_template
            for replace_this, with_this in dict_with_template_replacements.items():
                result = result.replace(replace_this, str(with_this))
            return result


