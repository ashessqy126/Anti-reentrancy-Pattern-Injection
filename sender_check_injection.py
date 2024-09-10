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



def add_ownable_contract(ct: Contract, raw_file:list, offset):
    ct_start_line = ct.source_mapping['lines'][0]
    insert_pos = ct_start_line + offset - 1
    inserted_content = ['contract INJECTED_Ownable{\n',
                        '    address private _owner;\n',
                        '    constructor () public {\n',
                        '        _owner = msg.sender;\n',
                        '    }\n',
                        '    modifier injected_onlyOwner() {\n',
                        '        require(_owner == msg.sender, "Ownable: caller is not the owner");\n',
                        '        _;\n',
                        '    }\n',
                        '}\n']
    replaced_file = raw_file[:insert_pos-1] + inserted_content + raw_file[insert_pos-1:]
    return replaced_file, offset + len(inserted_content)

def add_contract_inherit(ct: Contract, raw_file:list, offset):
    contract_header_line = ct.source_mapping['lines'][0] + offset
    already_inherited = False
    while True:
        if 'is' in raw_file[contract_header_line - 1]:
            already_inherited = True
        if '{' in raw_file[contract_header_line - 1]:
            break
        contract_header_line += 1
    insert_pos = raw_file[contract_header_line - 1].index('{')
    if already_inherited:
        new_contract_header = (raw_file[contract_header_line - 1][:insert_pos]
                               + ', INJECTED_Ownable ' + raw_file[contract_header_line - 1][insert_pos:])
    else:
        new_contract_header = (raw_file[contract_header_line - 1][:insert_pos]
                               + ' is INJECTED_Ownable ' + raw_file[contract_header_line - 1][insert_pos:])
    replaced_file = raw_file[:contract_header_line-1] + [new_contract_header] + raw_file[contract_header_line:]
    return replaced_file, offset

# def add_owner_var(ct: Contract, raw_file:list, offset):
#     # st_var = ct.state_variables_declared[0]
#     st_var_line = ct.source_mapping['lines'][0]
#     while True:
#         if '{' in raw_file[st_var_line + offset - 1]:
#             break
#         st_var_line += 1
#     replaced_file = raw_file[:st_var_line + offset] + ['    address private _owner;\n'] + raw_file[st_var_line + offset:]
#     return replaced_file, 1 + offset

# def modify_constructors(ct: )

# def add_modifier(ct: Contract, raw_file:list, offset):
#     f = ct.functions_and_modifiers_declared[0]
#     modifier_location = f.source_mapping['lines'][0] - 1
#     tab_num = f.source_mapping['starting_column']
#     tabs = ''.join([' ' for _ in range(tab_num)])
#     inserted_content = ['\n',
#                         tabs + 'modifier injected_sender_check(){\n',
#                         tabs + '    require(_owner == msg.sender);\n',
#                         tabs + '    _;\n',
#                         tabs + '}\n']
#
#     replaced_file = (raw_file[:(modifier_location + offset - 1)] + inserted_content
#                      + raw_file[modifier_location + offset - 1:])
#     return replaced_file, len(inserted_content) + offset

def _sender_check_modifier_injection(f: Function, raw_file:list, offset):
    # FN = cg.func2node[f]
    # FN_parent = FN.fathers
    function_header = f.source_mapping['lines'][0]
    # function_header = raw_file[func_line + offset - 1]
    while True:
        if 'returns' in raw_file[function_header + offset - 1] or '{' in raw_file[function_header + offset - 1]:
            break
        function_header += 1
    if 'returns' in raw_file[function_header + offset - 1]:
        insert_pos = raw_file[function_header + offset - 1].index('returns')
    else:
        insert_pos = raw_file[function_header + offset - 1].index('{')
    modifier_header = raw_file[function_header + offset - 1][:insert_pos] + ' injected_onlyOwner ' + raw_file[function_header + offset - 1][insert_pos:]
    replaced_file = raw_file[:function_header+offset-1] + [modifier_header] + raw_file[function_header+offset:]
    return replaced_file, offset

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def sender_check_modifier_injection(src_path, dest_path):
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
            func = c.function
            onlyOwner = False
            for m in func.modifiers:
                if str(m) == 'onlyOwner':
                    onlyOwner = True
            if not onlyOwner:
                tmp[c.function.contract] = tmp.get(c.function.contract, set()) | {func}
    offset = 0
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    replaced_file = raw_file
    if contracts:
        replaced_file, offset = add_ownable_contract(contracts[0], replaced_file, offset)
    for ct in contracts:
        replaced_file, offset = add_contract_inherit(ct, replaced_file, offset)
        external_calls = list(external_calls)
        external_calls = sorted(external_calls, key=lambda x: x.source_mapping['lines'][0])
        ct_ext_functions = tmp.get(ct, set())
        for f in ct_ext_functions:
            if isinstance(f, Modifier):
                cg = CallGraph(f.compilation_unit)
                cg.build_call_graph()
                f_fathers = cg.get_function_fathers(f)
                for ff in f_fathers:
                    replaced_file, offset = _sender_check_modifier_injection(ff, replaced_file, offset)
            else:
                replaced_file, offset = _sender_check_modifier_injection(f, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f.sol'
    dest_path = 'test.sol'
    sender_check_modifier_injection(src_path, dest_path)