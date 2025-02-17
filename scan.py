from detectors.reentrancy_eth import ReentrancyEth
import os
from slither.slither import Slither
import logging
from typing import List
from collections import namedtuple
from slither.core.cfg.node import Node
import solidity
from slither.core.solidity_types.mapping_type import MappingType
import re



FindingKey = namedtuple("FindingKey", ["function", "calls", "send_eth"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes"])

class reentrancy_call:
    def __init__(self, sl: Slither):
        self.sl = sl

    def extract(self):
        logger_detector = logging.getLogger("Detectors")
        extracted_calls = set()
        vars_written = set()
        for compilation_unit in self.sl.compilation_units:
            instance = ReentrancyEth(compilation_unit, self.sl, logger_detector)
            reentracies = instance.detect()
            varsWritten: List[FindingValue]
            tmp = set()
            for (function, calls, _), varsWritten in reentracies:
                calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
                for v in varsWritten:
                    for w in v.nodes:
                        for st in w.state_variables_written:
                            vars_written.add(str(st))
                # vars_written = '-'.join(vars_written)
                for (call_info, calls_list) in calls:
                    for c in calls_list:
                        # # if c == call_info:
                        # if c.function not in tmp:
                        extracted_calls.add(c)
                            # tmp.add(c.function)
                        # break
                        # break
                    # break
        return extracted_calls

    def extract_ex_calls_with_vars1(self):
        logger_detector = logging.getLogger("Detectors")
        extracted_calls = []
        var_written = []
        for compilation_unit in self.sl.compilation_units:
            instance = ReentrancyEth(compilation_unit, self.sl, logger_detector)
            reentracies = instance.detect()
            varsWritten: List[FindingValue]
            tmp = set()
            for (function, calls, _), varsWritten in reentracies:
                # calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
                # for (call_info, calls_list) in calls:
                #     for c in calls_list:
                v = ''
                # for t in varsWritten:
                #     v = t.variable
                v = list(varsWritten)[-1]
                v_to_type = 0
                v_from_type = 0 #address
                v_str = ''
                if(isinstance(v.variable.type, MappingType)):
                    if str(v.variable.type.type_from) == 'address':
                        v_from_type = 2
                    elif str(v.variable.type.type_from) == 'bytes32':
                        v_from_type = 3
                    else:
                        v_from_type = 4
                    if str(v.variable.type.type_to) == 'uint256':
                        v_to_type = 0
                    elif str(v.variable.type.type_to) == 'bool':
                        v_to_type = 1
                    else:
                        v_to_type = 0
                    pattern = f"{v.variable}\[(.*?)\]"
                    for n in v.nodes:
                        if 'delete' in str(n):
                            continue
                        if str(v.variable) in str(n):
                            n_str = str(n)[11:]
                            v_str = n_str.replace('=', ' ').split(' ')[0]
                        else:
                            n_str = str(n)[11:]
                            left = n_str.replace('=', ' ').split(' ')[0]
                            components = left.split('.')
                            if v_from_type == 2:
                                components[0] = f'{v.variable}[msg.sender]'
                            elif v_from_type == 3:
                                components[0] = f'{v.variable}[bytes32(0)]'
                            v_str = '.'.join(components)
                    if '.is' in v_str or '.Is' in v_str:
                        v_to_type = 1
                else:
                    v_str = str(v.variable)
                if v_str == '':
                    continue
                for (call_info, calls_list) in calls:
                    for c in calls_list:
                        if c not in tmp:
                            extracted_calls.append((c, v_str, v_from_type, v_to_type))
                            tmp.add(c)
                        # for st in w.state_variables_written:
                        # # if c == call_info:
                        # if c.function not in tmp:
                        # if c not in tmp:
                        #     extracted_calls.append((c, vars_written))
                        #     tmp.add(c)
                        # tmp.add(c.function)
                        # break
                        # break
                    # break
        extracted_calls = sorted(extracted_calls, key=lambda x: x[0].source_mapping['lines'][0])
        return extracted_calls

    def extract_ex_calls_with_vars(self):
        logger_detector = logging.getLogger("Detectors")
        extracted_calls = []
        var_written = []
        for compilation_unit in self.sl.compilation_units:
            instance = ReentrancyEth(compilation_unit, self.sl, logger_detector)
            reentracies = instance.detect()
            varsWritten: List[FindingValue]
            tmp = set()
            vars_written = set()
            for (function, calls, _), varsWritten in reentracies:
                # calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
                # for (call_info, calls_list) in calls:
                #     for c in calls_list:
                v = ''
                for t in varsWritten:
                    for n in t.nodes:
                        vars_written.add(n)
                for (call_info, calls_list) in calls:
                    for c in calls_list:
                        if c not in tmp:
                            extracted_calls.append((c, vars_written))
                            tmp.add(c)
                        # for st in w.state_variables_written:
                        # # if c == call_info:
                        # if c.function not in tmp:
                        # if c not in tmp:
                        #     extracted_calls.append((c, vars_written))
                        #     tmp.add(c)
                        # tmp.add(c.function)
                        # break
                        # break
                    # break
        extracted_calls = sorted(extracted_calls, key=lambda x: x[0].source_mapping['lines'][0])
        return extracted_calls


if __name__ == '__main__':
    solc_compiler = solidity.get_solc('etherscan/0x0a0b44bb51f857b0ca8aded28fdb90414afe9d40/0x0a0b44bb51f857b0ca8aded28fdb90414afe9d40.sol')
    sl = Slither('etherscan/0x0a0b44bb51f857b0ca8aded28fdb90414afe9d40/0x0a0b44bb51f857b0ca8aded28fdb90414afe9d40.sol',
                 solc=solc_compiler)
    scan_reentrancy = reentrancy_call(sl)
    dangerous_calls = scan_reentrancy.extract()
    # print(dangerous_calls)
    print('dangerous call:')
    for c in dangerous_calls:
        print('\t', c)
    # i = 0
    # for root, dirs, files in os.walk('etherscan/'):
    #     for file in files:
    #         if file.endswith('.sol'):
    #             i += 1
    #             print(f'scanning the {i}-th file: {file}-----------------')
    #             full_path = os.path.join(root, file)
    #             solc_version = solidity.get_solc(full_path)
    #             if solc_version is None:
    #                 print('cannot get a correct solc version')
    #                 continue
    #             try:
    #                 scan_reentrancy = reentrancy_call(Slither(full_path, solc = solc_version))
    #                 print(scan_reentrancy.extract())
    #             except Exception:
    #                 print(f'compilation for {full_path} failed')

    # scan_reentrancy = reentrancy_call(Slither('test.sol'))
    # print(scan_reentrancy.extract())