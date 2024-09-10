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

def add_time_var(ct: Contract, raw_file: list, offset):
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    uint256 public lastTime;\n'] + raw_file[
                                                                                                    st_var_line + offset:]
    return replaced_file, offset + 1

def _add_control(c: Node, raw_file:list, offset):
    c_line_start = c.source_mapping['lines'][0]
    c_line_end = c.source_mapping['lines'][-1]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    inserted_content = [tabs + 'require(block.timestamp >= lastTime + 500);\n',
                        tabs + 'lastTime = block.timestamp;\n']
    replaced_file = (raw_file[:c_line_start + offset - 1] \
                     + inserted_content
                     + raw_file[c_line_start + offset - 1:]);
    return replaced_file, offset + len(inserted_content)

def access_freq_control_injection(src_path, dest_path):
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
        contracts = list(tmp.keys())
        contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
        replaced_file = raw_file
        for ct in contracts:
            replaced_file, offset = add_time_var(ct, replaced_file, offset)
            ext_calls = tmp.get(ct, set())
            ext_calls = list(ext_calls)
            ext_calls = sorted(ext_calls, key=lambda x: x.source_mapping['lines'][0])
            for c in ext_calls:
                replaced_file, offset = _add_control(c, replaced_file, offset)
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
    src_path = './reentrancy_vul/spank_chain_payment.sol'
    dest_path = 'test.sol'
    access_freq_control_injection(src_path, dest_path)
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