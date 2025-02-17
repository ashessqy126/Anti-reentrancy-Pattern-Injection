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


#function transfer(address to, uint256 a) public{
#    _balances[address(this)] -= a;
#    _balances[to] += a;
#}
def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)
def add_interface(ct: Contract, raw_file:list, offset, version=5):
    ct_start_line = ct.source_mapping['lines'][0]
    insert_pos = ct_start_line + offset - 1
    if version < 5:
        inserted_content = ['interface IUniswapV2Router{\n',
                        '    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] path, address to, uint deadline) external;\n',
                        '}\n']
    else:
        inserted_content = ['interface IUniswapV2Router{\n',
                            '    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] calldata path, address to, uint deadline) external;\n',
                            '}\n']
    replaced_file = raw_file[:insert_pos] + inserted_content + raw_file[insert_pos:]
    return replaced_file, offset + len(inserted_content)

def add_path_var(ct:Contract, raw_file, offset, ver=5):
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    if ver < 5:
        replaced_file = (raw_file[:st_var_line + offset] + ['    address[] path = new address[](2);\n'] +
                     raw_file[st_var_line + offset:])
    else:
        replaced_file = (raw_file[:st_var_line + offset] + ['    address[] path = new address[](2);\n'] +
                         raw_file[st_var_line + offset:])
    return replaced_file, offset + 1

def add_high_level_transfer(ct: Contract, vars, raw_file:list, offset):
    f = ct.functions_and_modifiers_declared[0]
    function_location = f.source_mapping['lines'][0] - 1
    tab_num = f.source_mapping['starting_column']
    tabs = ''.join([' ' for _ in range(tab_num)])
    vars_new = []
    for v, t_from, t_to in vars:
        pattern = f"\[(.*?)\]"
        match = re.search(pattern, v)
        if match:
            if t_from == 3:
                vars_new.append((v.replace(match.group(1), 'bytes32(to)'), t_to))
            else:
                vars_new.append((v.replace(match.group(1), 'to'), t_to))
        else:
            vars_new.append((v, t_to))
    inserted_content = ['\n', tabs + 'function transfer1(address to, uint256 a) public{\n',
                        tabs + '//assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function\n']
    for var, t in vars_new:
        if t == 0:
            inserted_content += [tabs + f'    {var} = 0;\n']
        else:
            inserted_content += [tabs + f'    {var} = true;\n']
    inserted_content += [tabs + '}\n', '\n']
    replaced_file = raw_file[:(function_location + offset)] + inserted_content + raw_file[function_location + offset:]
    return replaced_file, offset + len(inserted_content)

# def add_balances_var(ct: Contract, raw_file:list, offset):
#     # mapping(address owner => uint256) private _balances;
#     st_var_line = ct.source_mapping['lines'][0]
#     while True:
#         if '{' in raw_file[st_var_line + offset - 1]:
#             break
#         st_var_line += 1
#     replaced_file = (raw_file[:st_var_line + offset] + ['    mapping(address owner => uint256) _balances;\n']
#                      + raw_file[st_var_line + offset:])
#     return replaced_file

def add_external_API_call_logic(c: Node, var, type, raw_file:list, offset):
    c_line_start = c.source_mapping['lines'][0]
    # c_line_end = c.source_mapping['lines'][-1]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    if type == 0:
        replaced_file = (raw_file[: c_line_start + offset - 1] + [tabs + f'if({var}==0) return;\n',
                                                              tabs + f'IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens({var}, path, msg.sender, block.timestamp);\n']
                         + raw_file[c_line_start + offset - 1:])
    else:
        replaced_file = (raw_file[: c_line_start + offset - 1] + [tabs + f'if({var}) return;\n',
                                                                  tabs + f'IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(10, path, msg.sender, block.timestamp);\n']
                         + raw_file[c_line_start + offset - 1:])
    return replaced_file, offset + 2

def external_state_sync_injection(src_path, dest_path):
    with open(src_path, 'r') as f:
        raw_file = f.readlines()
        solc_version = solidity.get_solc(src_path)
        ver = 5
        if 'v0.4.' in str(solc_version):
            ver = 4
        else:
            ver = 5
        try:
            sl = Slither(src_path, solc=str(solc_version))
        except Exception as e:
            print(f'compilation for {src_path} failed')
            return -1
        scan_reentrancy = reentrancy_call(sl)
        external_calls = scan_reentrancy.extract_ex_calls_with_vars1()
        tmp = {}
        vars = set()
        for c, v, t_from, t_to in external_calls:
            c: Node
            tmp[c.function.contract] = tmp.get(c.function.contract, []) + [(c, v, t_from, t_to)]
            vars.add((v, t_from, t_to))
    offset = 0
    contracts = list(tmp.keys())
    contracts = sorted(contracts, key=lambda x: x.source_mapping['lines'][0])
    replaced_file = raw_file
    replaced_file, offset = add_interface(contracts[0], replaced_file, offset, ver)
    for ct in contracts:
        replaced_file, offset = add_path_var(ct, replaced_file, offset, ver)
        replaced_file, offset = add_high_level_transfer(ct, vars, replaced_file, offset)

        external_calls = tmp.get(ct, set())
        for c, v, t_from, t_to in external_calls:
            replaced_file, offset = add_external_API_call_logic(c, v, t_to, replaced_file, offset)
    write_file(dest_path, replaced_file)
    return 0

if __name__ == '__main__':
    src_path = './reentrancy_vul/0xbe4041d55db380c5ae9d4a9b9703f1ed4e7e3888.sol'
    dest_path = 'test.sol'
    external_state_sync_injection(src_path, dest_path)
