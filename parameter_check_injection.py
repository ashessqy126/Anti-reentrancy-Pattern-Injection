import os.path

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import (Call, SolidityCall, Binary, BinaryType, Unary, LibraryCall,
                                        Assignment, InternalCall, TypeConversion, HighLevelCall, LowLevelCall,
                                        Index, Member)
from slither.slithir.operations.transfer import Transfer
from slither.core.solidity_types import ArrayType, ElementaryType, UserDefinedType, Type, MappingType
from slither.core.declarations import Contract, Function, Modifier
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables import Constant, TemporaryVariable
from CallGraph import CallGraph
import solidity
from scan import reentrancy_call
from slither.slither import Slither
import re

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def add_authorized_var(ct: Contract, raw_file:list, offset):
    # st_var = ct.state_variables_declared[0]
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    address _authorized = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;\n'] + raw_file[st_var_line + offset:]
    return replaced_file, offset + 1

def add_ECDSA_library(ct: Contract, raw_file:list, offset):
    ct_start_line = ct.source_mapping['lines'][0]
    insert_pos = ct_start_line + offset - 1
    inserted_content = ['library ECDSA{\n',
                        '    function recover(bytes32 hash, bytes memory signature) internal pure returns (address){\n',
                        '        if (signature.length == 65) {\n',
                        '            bytes32 r;\n',
                        '            bytes32 s;\n',
                        '            uint8 v;\n',
                        '            assembly {\n',
                        '                r := mload(add(signature, 0x20))\n',
                        '                s := mload(add(signature, 0x40))\n',
                        '                v := byte(0, mload(add(signature, 0x60)))\n',
                        '            }\n',
                        '            address signer = ecrecover(hash, v, r, s);\n',
                        '            if (signer == address(0)) {\n',
                        '                revert();\n',
                        '            }\n',
                        '        }\n',
                        '        else{\n',
                        '            revert();\n',
                        '        }\n',
                        '    }\n',
                        '}\n']
    replaced_file = raw_file[:insert_pos-1] + inserted_content + raw_file[insert_pos-1:]
    return replaced_file, offset + len(inserted_content)

def inject_function_parameters(f: Function, raw_file:list, offset):
    p_1 = 'bytes32 data'
    p_2 = 'bytes memory signature'
    p1 = re.compile(r'[(](.*?)[)]', re.S)  #最小匹配
    if len(f.parameters) == 0:
        f_sline = f.source_mapping['lines'][0]
        while True:
            matchObj = re.findall(p1, raw_file[f_sline + offset - 1])
            if matchObj:
                break
            f_sline += 1
        modified_func_header = raw_file[f_sline + offset - 1].replace(f'({matchObj[0]})', f'({p_1}, {p_2})')
        replaced_file = raw_file[:f_sline+offset-1] + [modified_func_header] + raw_file[f_sline+offset:]
    else:
        last_p = f.parameters[-1]
        last_p_line = last_p.source_mapping['lines'][0]
        last_p_col = last_p.source_mapping['ending_column']
        modified_func_header = raw_file[last_p_line+offset-1][0:last_p_col-1] + f', {p_1}, {p_2}' + raw_file[last_p_line+offset-1][last_p_col-1:]
        replaced_file = raw_file[:last_p_line+offset-1] + [modified_func_header] + raw_file[last_p_line+offset:]
    return replaced_file, offset

def add_parameter_check(f: Function, raw_file:list, offset):
    f_sline = f.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[f_sline + offset - 1]:
            break
        f_sline += 1
    insert_pos = f_sline + 1
    tab_num = f.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num - 1)])
    inserted_content = [tabs + '    require(ECDSA.recover(data, signature) == _authorized);\n']
    replaced_file = (raw_file[:insert_pos+offset-1] +  inserted_content + raw_file[insert_pos+offset-1:])
    return replaced_file, offset + len(inserted_content)


def parameter_check_injection(src_path, dest_path):
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
            tmp[c.function.contract] = tmp.get(c.function.contract, set()) | {c.function}
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    offset = 0
    replaced_file = raw_file
    replaced_file, offset = add_ECDSA_library(contracts[0], replaced_file, offset)
    for ct in contracts:
        replaced_file, offset = add_authorized_var(ct, replaced_file, offset)
        ct_ext_functins = tmp.get(ct, set())
        outter_functions = set()
        cg = CallGraph(ct.compilation_unit)
        cg.build_call_graph()
        for f in ct_ext_functins:
            outtest_fathers = cg.get_outtest_function_fathers(f)
            for ff in outtest_fathers:
                outter_functions.add(ff)
        outtest_functions = list(outter_functions)
        outtest_functions = sorted(outtest_functions, key=lambda x: x.source_mapping['lines'][0])
        for f in outtest_functions:
            replaced_file, offset = inject_function_parameters(f, replaced_file, offset)
            replaced_file, offset = add_parameter_check(f, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/reentrancy_bonus.sol'
    dest_path = 'test.sol'
    parameter_check_injection(src_path, dest_path)