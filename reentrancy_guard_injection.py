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

def add_reentrancy_guard_contract(ct: Contract, raw_file:list, offset):
    ct_start_line = ct.source_mapping['lines'][0]
    insert_pos = ct_start_line + offset - 1
    inserted_content = ['contract ReentrancyGuard{\n',
                        '    uint256 private constant _NOT_ENTERED = 1;\n',
                        '    uint256 private constant _ENTERED = 2;\n',
                        '    uint256 private _status;\n',
                        '    constructor() public{\n',
                        '         _status = _NOT_ENTERED;\n',
                        '    }\n',
                        '    modifier nonReentrant() {\n',
                        '        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");\n',
                        '        _status = _ENTERED;\n',
                        '        _;\n',
                        '       _status = _NOT_ENTERED;\n',
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
                               + ', ReentrancyGuard ' + raw_file[contract_header_line - 1][insert_pos:])
    else:
        new_contract_header = (raw_file[contract_header_line - 1][:insert_pos]
                               + ' is ReentrancyGuard ' + raw_file[contract_header_line - 1][insert_pos:])
    replaced_file = raw_file[:contract_header_line-1] + [new_contract_header] + raw_file[contract_header_line:]
    return replaced_file, offset


def inject_nonreentrant_modifier(f: Function, raw_file:list, offset):
    function_header = f.source_mapping['lines'][0]
    while True:
        if 'returns' in raw_file[function_header + offset - 1] or '{' in raw_file[function_header + offset - 1]:
            break
        function_header += 1
    if 'returns' in raw_file[function_header + offset - 1]:
        insert_pos = raw_file[function_header + offset - 1].index('returns')
    else:
        insert_pos = raw_file[function_header + offset - 1].index('{')
    modifier_header = raw_file[function_header + offset - 1][:insert_pos] + ' nonReentrant ' + raw_file[function_header + offset - 1][insert_pos:]
    replaced_file = raw_file[:function_header + offset - 1] + [modifier_header] + raw_file[function_header + offset:]
    return replaced_file, offset

def reentrancy_guard_injection(src_path, dest_path):
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
    offset = 0
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    replaced_file = raw_file
    replaced_file, offset = add_reentrancy_guard_contract(contracts[0], replaced_file, offset)
    for ct in contracts:
        replaced_file, offset = add_contract_inherit(ct, replaced_file, offset)
        ct_ext_functins = tmp.get(ct, set())
        for f in ct_ext_functins:
            if isinstance(f, Modifier):
                cg = CallGraph(f.compilation_unit)
                cg.build_call_graph()
                f_fathers = cg.get_function_fathers(f)
                for ff in f_fathers:
                    replaced_file, offset = inject_nonreentrant_modifier(ff, replaced_file, offset)
            else:
                replaced_file, offset = inject_nonreentrant_modifier(f, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/reentrancy_insecure.sol'
    dest_path = 'test.sol'
    reentrancy_guard_injection(src_path, dest_path)
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