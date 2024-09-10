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

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def add_price_var(ct: Contract, raw_file: list, offset):
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    uint256 public SALE_PRICE = 0.002 ether;\n'] + raw_file[
                                                                                                    st_var_line + offset:]
    return replaced_file, offset + 1

def _add_price_control(c: Node, raw_file:list, offset):
    c_line_start = c.source_mapping['lines'][0]
    c_line_end = c.source_mapping['lines'][-1]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    inserted_content = [tabs + 'require(msg.value >= SALE_PRICE);\n']
    replaced_file = (raw_file[:c_line_start + offset - 1] \
                     + inserted_content
                     + raw_file[c_line_start + offset - 1:]);
    return replaced_file, offset + len(inserted_content)

def modify_function_to_payable(f: Function, raw_file:list, offset):
    function_header = f.source_mapping['lines'][0]
    # function_header = raw_file[func_line + offset - 1]
    while True:
        if 'returns' in raw_file[function_header + offset - 1] or '{' in raw_file[function_header + offset - 1]:
            break
        if 'payable' in  raw_file[function_header + offset - 1]:
            return raw_file, offset
        function_header += 1
    if 'payable' in raw_file[function_header + offset - 1]:
        return raw_file, offset
    if 'returns' in raw_file[function_header + offset - 1]:
        insert_pos = raw_file[function_header + offset - 1].index('returns')
    else:
        insert_pos = raw_file[function_header + offset - 1].index('{')
    modifier_header = (raw_file[function_header + offset - 1][:insert_pos] + ' payable ' +
                       raw_file[function_header + offset - 1][insert_pos:])
    replaced_file = raw_file[:function_header + offset - 1] + [modifier_header] + raw_file[function_header + offset:]
    return replaced_file, offset

def access_price_injection(src_path, dest_path):
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
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    replaced_file = raw_file

    for ct in contracts:
        replaced_file, offset = add_price_var(ct, replaced_file, offset)
        function_dict = tmp.get(ct, set())
        functions = list(function_dict.keys())
        functions = sorted(functions, key=lambda x: x.source_mapping['lines'][0])
        for f in functions:
            if isinstance(f, Modifier):
                cg = CallGraph(f.compilation_unit)
                cg.build_call_graph()
                f_fathers = cg.get_function_fathers(f)
                for ff in f_fathers:
                    replaced_file, offset = modify_function_to_payable(ff, replaced_file, offset)
            else:
                replaced_file, offset = modify_function_to_payable(f, replaced_file, offset)
            nodes = function_dict.get(f, set())
            nodes = list(nodes)
            nodes = sorted(nodes, key=lambda x: x.source_mapping['lines'][0])
            for n in nodes:
                replaced_file, offset = _add_price_control(n, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0

# def reentrancy_guard_injection(src_path, dest_path):
#     with open(src_path, 'r') as f:
#         raw_file = f.readlines()
#         solc_version = solidity.get_solc(src_path)
#         try:
#             sl = Slither(src_path, solc=str(solc_version))
#         except Exception as e:
#             print(f'compilation for {src_path} failed')
#             return -1
#         scan_reentrancy = reentrancy_call(sl)
#         external_calls = scan_reentrancy.extract()
#         tmp = {}
#         for c in external_calls:
#             c: Node
#             tmp[c.function.contract] = tmp.get(c.function.contract, set()) | {c.function}
#     offset = 0
#     contracts = list(tmp.keys())
#     contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
#     replaced_file = raw_file
#     replaced_file, offset = add_reentrancy_guard_contract(contracts[0], replaced_file, offset)
#     for ct in contracts:
#         replaced_file, offset = add_contract_inherit(ct, replaced_file, offset)
#         ct_ext_functins = tmp.get(ct, set())
#         for f in ct_ext_functins:
#             if isinstance(f, Modifier):
#                 cg = CallGraph(f.compilation_unit)
#                 cg.build_call_graph()
#                 f_fathers = cg.get_function_fathers(f)
#                 for ff in f_fathers:
#                     replaced_file, offset = inject_nonreentrant_modifier(ff, replaced_file, offset)
#             else:
#                 replaced_file, offset = inject_nonreentrant_modifier(f, replaced_file, offset)
#     write_file(dest_path, replaced_file)
#     return 0

if __name__ == '__main__':
    src_path = './reentrancy_vul/reentrancy_insecure.sol'
    dest_path = 'test.sol'
    access_price_injection(src_path, dest_path)
    # reentrancy_guard_injection(src_path, dest_path)
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