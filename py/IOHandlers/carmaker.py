import re

from .base import BaseHandler


class CarMakerHandler(BaseHandler):
    def __init__(self, carmaker_file, param_file):
        super().__init__(carmaker_file, param_file)

    def load_data_file(self, data_file_path):
        with open(data_file_path, 'r') as data_file:
            lines = data_file.readlines()
            data = _parse_carmaker_data(lines)
        return data

    def apply_param_instances_to_data(self, param_instances):
        for parameter_key, value in param_instances.items():
            index_count = parameter_key.count('[')
            if index_count > 0:  # parameter is of array or matrix type e.g. "my.parameter[0][1] = 'norm(1,2)'"
                data_parameter_key = re.findall('(.*?)\[', parameter_key)[0]
                parameter_indeces = list(map(int, re.findall('\[([0-9]+)\]', parameter_key)))
                if index_count == 1:
                    self.data[data_parameter_key][parameter_indeces[0]] = value
                elif index_count == 2:
                    self.data[data_parameter_key][parameter_indeces[0]][parameter_indeces[1]] = value
            else:
                self.data[parameter_key] = value

    def write_data(self, path):
        with open(path, 'w') as testrun_file:
            testrun_file.write(self.data['#INFOFILE_HEADER'])
            indentation = False  # This line is added by Para.Dis. Add indentation to the testrun file where it is needed.
            for k, v in self.data.items():
                if indentation == True:
                    testrun_file.write('\t')
                    _write_single_line(k, v, testrun_file)
                    indentation = False
                    continue
                if k == '#INFOFILE_HEADER':
                    continue
                if type(v) is list and len(v):
                    if v == [[]]:
                        indentation = True
                    if type(v[0]) is list:
                        _write_multirow_line(k, v, testrun_file)
                    else:
                        _write_array(k, v, testrun_file)
                else:
                    _write_single_line(k, v, testrun_file)

    def get_data_value(self, data_key):
        return self.data.xpath(data_key)[0]


def _write_single_line(parameter_key, value, testrun_file):
    testrun_file.write(f'{parameter_key} = {value}\n')


def _write_multirow_line(parameter_key, value_matrix, testrun_file):
    testrun_file.write(f'{parameter_key}:\n')
    for value_row in value_matrix:
        if len(value_row) == 0:
            continue
        testrun_file.write(f'\t{" ".join([str(value) for value in value_row])}\n')


def _write_array(parameter_key, values, testrun_file):
    testrun_file.write(f'{parameter_key} = {" ".join([str(value) for value in values])}\n')


def _parse_carmaker_data(lines):
    data_dict = {}
    multirow_active = False
    for line_idx, line in enumerate(lines):
        if '=' in line:
            if multirow_active:  # finalize multirow entry before parsing current line
                if len(parsed_entry[multirow_key]) == 0:  # check if matrix has any rows
                    parsed_entry[multirow_key].append([])  # add empty row to create empty matrix, otherwise this parameter would be output as single line paramter
                data_dict.update(parsed_entry)
                del multirow_key  # just some data cleanup so its not in memory when parsing single lines
                multirow_active = False
            parsed_entry = _parse_single_line(line)
            data_dict.update(parsed_entry)
        elif ':' in line:
            multirow_active = True
            multirow_key = line.replace(':', '').strip()
            parsed_entry = {multirow_key: []}
        elif '#INFOFILE' in line:
            data_dict.update({'#INFOFILE_HEADER': line})  # on write this item needs to be handled separately, so its not confused with a parameter
        else:
            parsed_entry[multirow_key].append(_parse_multirow_line(line))
    return data_dict


def _parse_single_line(line):
    key, values_string = line.split('=', 1)
    key = key.strip()
    values_string = values_string.strip()
    values_strings = values_string.split(' ')
    values = [_parse_value(value) for value in values_strings]
    if len(values) == 1:
        values = values[0]
    return {key: values}


def _parse_multirow_line(line):
    values_string = line.strip()
    values_strings = values_string.split(' ')
    values = [_parse_value(value) for value in values_strings]
    return values


def _parse_value(value):
    try:
        if str(float(value)) == value:
            return float(value)
    except:
        pass
    try:
        if str(int(value)) == value:
            return int(value)
    except:
        pass
    return value  # value is assumed String
