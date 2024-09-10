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
def get_info_from_external_call(node: Node):
    for ir in node.irs:
        if isinstance(ir, HighLevelCall) or isinstance(ir, LowLevelCall):
            return ir.destination, ir.expression, ir.call_value
    return None, None

def normalize_node_expr(node: Node):
    RESERVED = ["&&", "||", '!=', '==', 'msg.sender', 'tx.origin']
    node_expr = str(node.expression).replace('require(bool,string)', 'require')
    # var_written = None
    # words = split_words(node_expr, RESERVED)
    for ir in node.irs:
        # if isinstance(ir, Assignment):
        #     var_written = ir.lvalue
        for r in ir.read:
            if isinstance(ir, Index) or isinstance(ir, Member):
                continue
            if isinstance(r, Constant) and isinstance(r.value, str) and len(r.value) > 0:
                # print(ir, type(ir), r, r.type)
                node_expr = node_expr.replace(r.value, f'"{r}"')
    if node.type == NodeType.VARIABLE:
        node_expr = str(node.variable_declaration.type) + ' ' + node_expr
    return node_expr

def get_modified_source_code(node: Node):
    # if node is None or node.expression is None:
    #     return None
    c, sub_expression, call_value = get_info_from_external_call(node)
    if isinstance(c, ReferenceVariable):
        c_name = find_ref_points_to(c, node)
    elif isinstance(c, TemporaryVariable):
        c = find_tmp_points_to(c, node)
        c_name = c.name
    else:
        c_name = c.name
    # node_expr = normalize_node_expr(node)

    # print(call_value)
    if call_value is None:
        transfer_amount = '0'
    else:
        if isinstance(call_value, ReferenceVariable):
            transfer_amount = find_ref_points_to(call_value, node)
        else:
            transfer_amount = call_value.name
        # transfer_amount = call_value
    # node_expr = str(node.expression).replace('require(bool,string)', 'require')
    # print('test', node_expr)
    if hasattr(c, 'type') and isinstance(c.type, UserDefinedType) and isinstance(c.type.type, Contract):
        return f'address({c_name}).send({transfer_amount})'
    elif hasattr(c, 'type') and c.type.name == 'address':
        # print(node.expression, sub_expression)
        return f'{c_name}.send({transfer_amount})'
    else:
        return None

# def get_modified_source_code(node: Node):
#     if node is None or node.expression is None:
#         return None
#     c, sub_expression, call_value = get_info_from_external_call(node)
#     if isinstance(c, ReferenceVariable):
#         c_name = find_ref_points_to(c, node)
#     else:
#         c_name = c.name
#     node_expr = normalize_node_expr(node)
#
#     # print(call_value)
#     if call_value is None:
#         transfer_amount = '0'
#     else:
#         if isinstance(call_value, ReferenceVariable):
#             transfer_amount = find_ref_points_to(call_value, node)
#         else:
#             transfer_amount = call_value.name
#         # transfer_amount = call_value
#     # node_expr = str(node.expression).replace('require(bool,string)', 'require')
#     # print('test', node_expr)
#     if hasattr(c, 'type') and isinstance(c.type, UserDefinedType) and isinstance(c.type.type, Contract):
#         return str(node_expr).replace(str(sub_expression), f'address({c_name}).send({transfer_amount})')
#     elif hasattr(c, 'type') and c.type.name == 'address':
#         # print(node.expression, sub_expression)
#         return str(node_expr).replace(str(sub_expression), f'{c_name}.send({transfer_amount})')
#     else:
#         return None

def get_node_source_info(node: Node):
    # print(c.source_mapping)
    # for ir in node.irs:
    #     if isinstance(ir, HighLevelCall) or isinstance(ir, LowLevelCall):
    #         print(ir.expression)
    return node.source_mapping['lines'][0], node.source_mapping['lines'][-1], node.source_mapping['starting_column'], ir.expression.source_mapping['ending_column']


def get_ir_source_info(ir):
    return ir.expression.source_mapping['lines'][0], ir.expression.source_mapping['lines'][-1], ir.expression.source_mapping['starting_column'], ir.expression.source_mapping['ending_column']

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

def get_external_call_position(node: Node):
    for ir in node.irs:
        if isinstance(ir, LowLevelCall) or isinstance(ir, HighLevelCall):
            return get_ir_source_info(ir)

def replace(sl: Slither, raw_file:list):
    # print(raw_file[18])
    scan_reentrancy = reentrancy_call(sl)
    previous_end = 0
    replaced_file = []
    external_calls = scan_reentrancy.extract()
    external_calls = list(external_calls)
    external_calls = sorted(external_calls, key=lambda x: x.source_mapping['lines'][0])
    for c in external_calls:
        c: Node
        # print('expression:', c, c.source_mapping)
        start_line, end_line, start_col, end_col = get_external_call_position(c)
        modified_c = get_modified_source_code(c)
        # print(c, modified_c)
        modified_c = raw_file[start_line-1][:start_col-1] + modified_c + raw_file[end_line-1][end_col-1:]
        # print(modified_c)
        # modified_c.replace('bool success,', 'bool success')
        matchObj = re.search('\(bool\s*(\w*),\s*\)', modified_c)
        if matchObj:
            modified_c = modified_c.replace(matchObj.group(), f'bool {matchObj.group(1)}')
        if modified_c is None:
            return None
        else:
            replaced_file = (replaced_file + raw_file[previous_end:start_line-1] +
                             [modified_c])
            previous_end = end_line
    replaced_file = replaced_file + raw_file[previous_end:]
    # print(len(replaced_file))
    return replaced_file

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            # i += 1
            # print(i, l)
            f.write(l)

def modify_safe_transfer(src_path, dest_path):
    with open(src_path, 'r') as f:
        raw_file = f.readlines()
        solc_version = solidity.get_solc(src_path)
        try:
            sl = Slither(src_path, solc=str(solc_version))
        except Exception as e:
            print(f'compilation for {src_path} failed')
            return -1
        replaced_file = replace(sl, raw_file)
        # print('total_len:', len(replaced_file))
        write_file(dest_path, replaced_file)
    return 0



if __name__ == '__main__':
    src_path = './reentrancy_vul/reentrancy_insecure.sol'
    dest_path = 'test.sol'
    modify_safe_transfer(src_path, dest_path)
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