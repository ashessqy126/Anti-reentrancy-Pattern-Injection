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


def add_mutex_var(ct: Contract, raw_file:list, offset):
    # st_var = ct.state_variables_declared[0]
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    bool _injected_mutex_var = false;\n'] + raw_file[st_var_line + offset:]
    return replaced_file, 1 + offset

def add_modifier(ct: Contract, raw_file:list, offset):
    f = ct.functions_and_modifiers_declared[0]
    modifier_location = f.source_mapping['lines'][0] - 1
    tab_num = f.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num)])
    replaced_file = raw_file[:(modifier_location + offset - 1)] + ['\n', tabs + 'modifier injected_swap(){\n',
                                                                 tabs + '    _injected_mutex_var = true;\n',
                                                                 tabs + '    _;\n',
                                                                 tabs + '    _injected_mutex_var = false;\n',
                                                                 tabs + '}\n'] + raw_file[modifier_location + offset - 1:]
    return replaced_file, 6 + offset

def _mutex_modifier_injection(f: Function, raw_file:list, offset):
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
    modifier_header = raw_file[function_header + offset - 1][:insert_pos] + ' injected_swap' + ' ' + raw_file[function_header + offset - 1][insert_pos:]
    replaced_file = raw_file[:function_header+offset-1] + [modifier_header] + raw_file[function_header+offset:]
    return replaced_file, offset

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def add_check_before_external_call(c: Node, raw_file:list, offset):
    c_start_line = c.source_mapping['lines'][0]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    replaced_file = (raw_file[:c_start_line+offset-1] + [tabs + 'require(_injected_mutex_var);\n']
                     + raw_file[c_start_line+offset-1:])
    return replaced_file, offset + 1


def mutex_modifier_injection(src_path, dest_path):
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
            function_dict = tmp.get(c.function.contract, dict())
            node_set = function_dict.get(c.function, set())
            node_set.add(c)
            function_dict[c.function] = node_set
            tmp[c.function.contract] = function_dict
    offset = 0
    replaced_file = raw_file
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    for ct in contracts:
        replaced_file, offset = add_mutex_var(ct, replaced_file, offset)
        replaced_file, offset = add_modifier(ct, replaced_file, offset)
        function_dict = tmp.get(ct, set())
        functions = list(function_dict.keys())
        functions = sorted(functions, key=lambda x: x.source_mapping['lines'][0])
        for f in functions:
            if isinstance(f, Modifier):
                cg = CallGraph(f.compilation_unit)
                cg.build_call_graph()
                f_fathers = cg.get_function_fathers(f)
                for ff in f_fathers:
                    replaced_file, offset = _mutex_modifier_injection(ff, replaced_file, offset)
            else:
                replaced_file, offset = _mutex_modifier_injection(f, replaced_file, offset)
            nodes = function_dict.get(f, set())
            nodes = list(nodes)
            nodes = sorted(nodes, key=lambda x: x.source_mapping['lines'][0])
            for n in nodes:
                replaced_file, offset = add_check_before_external_call(n, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/modifier_reentrancy.sol'
    dest_path = 'test.sol'
    mutex_modifier_injection(src_path, dest_path)
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