import os.path

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import (Call, SolidityCall, Binary, BinaryType, Unary, LibraryCall,
                                        Assignment, InternalCall, TypeConversion, HighLevelCall, LowLevelCall,
                                        Index, Member, Delete)
from slither.slithir.operations.transfer import Transfer
from slither.core.solidity_types import ArrayType, ElementaryType, UserDefinedType, Type, MappingType
from slither.core.declarations import Contract, Function, Modifier
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables import Constant, TemporaryVariable
from slither.core.variables.local_variable import LocalVariable
from CallGraph import CallGraph
import solidity
from scan import reentrancy_call
from slither.slither import Slither


def extract_state_var(c: Node):
    st = None
    func = c.function
    for ir in c.irs:
        if isinstance(ir, Delete):
            st = ir.variable
        elif ir.lvalue:
            st = ir.lvalue
    return st

def add_check_for_uint(ct: Contract, raw_file:list, offset):
    f = ct.functions_and_modifiers_declared[0]
    func_location = f.source_mapping['lines'][0]
    tab_num = f.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num)])
    inserted_content = ['\n',
                        tabs + 'function checkForV1(uint v) internal{\n',
                        tabs + '    require(v != 0);\n',
                        tabs + '}\n']
    replaced_file = (raw_file[:(func_location + offset - 1)] + inserted_content
                     + raw_file[func_location + offset - 1:])
    return replaced_file, len(inserted_content) + offset

def add_check_for_bool(ct: Contract, raw_file:list, offset):
    f = ct.functions_and_modifiers_declared[0]
    func_location = f.source_mapping['lines'][0]
    tab_num = f.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num)])
    inserted_content = ['\n',
                        tabs + 'function checkForV2(bool v) internal{\n',
                        tabs + '    require(v != false);\n',
                        tabs + '}\n']

    replaced_file = (raw_file[:(func_location + offset - 1)] + inserted_content
                     + raw_file[func_location + offset - 1:])
    return replaced_file, len(inserted_content) + offset

def add_var_update_before_call(c: Node, vars_written, raw_file:list, offset):
    c_start_line = c.source_mapping['lines'][0]
    tab_num = c.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num-1)])
    insert_pos = c_start_line
    insert_update = []
    insert_check = []
    for v_type, v in vars_written:
        if isinstance(v_type, ElementaryType) and 'int' in str(v_type):
            insert_update += [tabs + f'{v} = 0;\n']
            insert_check += [tabs + f'checkForV1({v});\n']
        elif isinstance(v_type, ElementaryType) and 'bool' in str(v_type):
            insert_update += [tabs + f'{v} = false;\n']
            insert_check += [tabs + f'checkForV2({v});\n']

    replaced_file = raw_file[:insert_pos+offset-1] + insert_check + insert_update + raw_file[insert_pos+offset-1:]
    return replaced_file, offset + len(insert_check) + len(insert_update)

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)

def find_tmp_points_to(r: TemporaryVariable, node: Node):
    for ir in node.irs:
        if isinstance(ir, TypeConversion):
            if ir.lvalue == r:
                return ir.variable

def find_ref_points_to(r: ReferenceVariable, node: Node):
    tmp = {}
    for ir in node.irs:
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

def intermedi_state_update_injection(src_path, dest_path):
    with open(src_path, 'r') as f:
        raw_file = f.readlines()
        solc_version = solidity.get_solc(src_path)
        try:
            sl = Slither(src_path, solc=str(solc_version))
        except Exception as e:
            print(f'compilation for {src_path} failed')
            return -1
        scan_reentrancy = reentrancy_call(sl)
        external_calls = scan_reentrancy.extract_ex_calls_with_vars()

        external_calls = list(external_calls)
        external_calls = sorted(external_calls, key=lambda x: x[0].source_mapping['lines'][0])
        
        processed_contracts = set()
        replaced_file = raw_file
        offset = 0

        for c, varsWritten in external_calls:
            if c.function.contract not in processed_contracts:
                replaced_file, offset = add_check_for_uint(c.function.contract, replaced_file, offset)
                replaced_file, offset = add_check_for_bool(c.function.contract, replaced_file, offset)
                processed_contracts.add(c.function.contract)
            for n in varsWritten:
                written_vars = set()
                var = extract_state_var(n)
                var_type = var.type
                if isinstance(var, ReferenceVariable):
                    var_name = find_ref_points_to(var, n)
                elif isinstance(var, TemporaryVariable):
                    var = find_tmp_points_to(var, n)
                    var_name = var.name
                else:
                    var_name = var.name
                written_vars.add((var_type, var_name))
            replaced_file, offset = add_var_update_before_call(c, written_vars, replaced_file, offset)

    write_file(dest_path, replaced_file)
    return 0


if __name__ == '__main__':
    src_path = './reentrancy_vul/spank_chain_payment.sol'
    dest_path = 'test.sol'
    intermedi_state_update_injection(src_path, dest_path)