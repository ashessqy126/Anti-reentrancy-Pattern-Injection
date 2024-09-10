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

def add_fixed_addr_var(ct: Contract, raw_file:list, offset):
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    address _fixed_address = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;\n'] + raw_file[st_var_line + offset:]
    return replaced_file, 1 + offset

def find_tmp_points_to(r: TemporaryVariable, node: Node):
    for ir in node.irs:
        if isinstance(ir, TypeConversion):
            if ir.lvalue == r:
                return ir.variable

def find_ref_points_to(r: ReferenceVariable, node: Node):
    tmp = {}
    for ir in node.irs:
        # print(tmp)
        if isinstance(ir, Index):
            var = ir.read[0]
            index = ir.read[1]
            var_name = var.name
            index_name = index.name
            if isinstance(var, ReferenceVariable):
                var_name = tmp.get(var)
            if isinstance(index, ReferenceVariable):
                index_name = tmp.get(index)
            tmp[ir.lvalue] = f'{var_name}[{index_name}]'
        if isinstance(ir, Member):
            var = ir.variable_left
            member = ir.variable_right
            var_name = var.name
            member_name = member.name
            if isinstance(var, ReferenceVariable):
                var_name = tmp.get(var)
            if isinstance(member, ReferenceVariable):
                member_name = tmp.get(member)
            tmp[ir.lvalue] = f'{var_name}.{member_name}'
    return tmp.get(r)

def fix_dest_addr(c: Node, raw_file:list, offset):
    dest_addr = None
    for ir in c.irs:
        if isinstance(ir, LowLevelCall) or isinstance(ir, HighLevelCall):
            dest_addr = ir.destination
            break
    if isinstance(dest_addr, ReferenceVariable):
        dest_addr_str = find_ref_points_to(dest_addr, c)
    elif isinstance(dest_addr, TemporaryVariable):
        dest_addr = find_tmp_points_to(dest_addr, c)
        dest_addr_str = dest_addr.name
    else:
        dest_addr_str = str(dest_addr)
    # print(dest_addr_str, dest_addr.type)
    # start_column = dest_addr.source_mapping['starting_column']
    # end_column = dest_addr.source_mapping['ending_column']
    c_line = c.source_mapping['lines'][0]
    modified_c = raw_file[c_line+offset-1].replace(dest_addr_str, f'{dest_addr.type}(_fixed_address)')
    replaced_file = raw_file[:c_line+offset-1] + [modified_c] + raw_file[c_line+offset:]
    return replaced_file, offset

def fixed_contract_injection(src_path, dest_path):
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
        replaced_file, offset = add_fixed_addr_var(ct, replaced_file, offset)
        external_calls = tmp.get(ct, set())
        external_calls = list(external_calls)
        external_calls = sorted(external_calls, key=lambda x: x.source_mapping['lines'][0])
        for c in external_calls:
            replaced_file, offset = fix_dest_addr(c, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0

if __name__ == '__main__':
    src_path = './reentrancy_vul/spank_chain_payment.sol'
    dest_path = 'test.sol'
    fixed_contract_injection(src_path, dest_path)