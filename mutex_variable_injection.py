import os.path

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import (Call, SolidityCall, Binary, BinaryType, Unary, LibraryCall,
                                        Assignment, InternalCall, TypeConversion, HighLevelCall, LowLevelCall,
                                        Index, Member)
from slither.slithir.operations.transfer import Transfer
from slither.core.solidity_types import ArrayType, ElementaryType, UserDefinedType, Type, MappingType
from slither.core.declarations import Contract
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables import Constant, TemporaryVariable

import solidity
from scan import reentrancy_call
from slither.slither import Slither
import re
# from split_words import split_words

def add_mutex_var(ct: Contract, raw_file:list, offset):
    # st_var = ct.state_variables_declared[0]
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    bool _injected_mutex_var = false;\n'] + raw_file[st_var_line + offset:]
    return replaced_file

def mutex_logic_injection(c: Node, raw_file:list, offset):
    # print(raw_file[18])
    c_line_start = c.source_mapping['lines'][0]
    c_line_end = c.source_mapping['lines'][-1]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    replaced_file = (raw_file[: c_line_start + offset - 1] + [tabs + 'require(_injected_mutex_var);\n',
                                                              tabs + '_injected_mutex_var = true;\n']
                     + raw_file[c_line_start + offset - 1: c_line_end + offset] +
                     [tabs + '_injected_mutex_var = false;\n'] +
                     raw_file[c_line_end + offset:])
    return replaced_file

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def mutex_var_injection(src_path, dest_path):
    with open(src_path, 'r') as f:
        raw_file = f.readlines()
        solc_version = solidity.get_solc(src_path)
        try:
            sl = Slither(src_path, solc=str(solc_version))
        except Exception as e:
            print(f'compilation for {src_path} failed')
            return -1
        scan_reentrancy = reentrancy_call(sl)
        external_calls = scan_reentrancy.extract()
        tmp = {}
        for c in external_calls:
            c: Node
            tmp[c.function.contract] = tmp.get(c.function.contract, set()) | {c}
    offset = 0
    replaced_file = raw_file
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    for ct in contracts:
        replaced_file = add_mutex_var(ct, replaced_file, offset)
        offset += 1
        external_calls = tmp.get(ct, set())
        external_calls = list(external_calls)
        external_calls = sorted(external_calls, key=lambda x: x.source_mapping['lines'][0])
        for c in external_calls:
            replaced_file = mutex_logic_injection(c, replaced_file, offset)
            offset += 3
    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/0xbaf51e761510c1a11bf48dd87c0307ac8a8c8a4f.sol'
    dest_path = 'test.sol'
    mutex_var_injection(src_path, dest_path)
    # solc_version = solidity.get_solc(fpath)
    # # print(Slither.version)
    # # print(fpath)
    # # solc_version = os.path.basename((solc_version))
    # sl = Slither(fpath, solc=str(solc_version))
    # # print('fpath')
    # scan_reentrancy = reentrancy_call(sl)
    # external_calls = scan_reentrancy.extract()
    # for c in external_calls:
    #     # print(c, end=' ')
    #     start_line, end_line = get_source_info(c)
    #     print(start_line, end_line)
    # print('hahah')
        # return -1