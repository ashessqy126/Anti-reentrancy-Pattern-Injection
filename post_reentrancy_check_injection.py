from slither.core.cfg.node import Node
import solidity
from scan import reentrancy_call
from slither.slither import Slither

def write_file(fpath, replaced_file: list):
    # i = 0
    with open(fpath, 'w') as f:
        for l in replaced_file:
            f.write(l)
def add_pre_var(ct, raw_file:list, offset):
    st_var_line = ct.source_mapping['lines'][0]
    while True:
        if '{' in raw_file[st_var_line + offset - 1]:
            break
        st_var_line += 1
    replaced_file = raw_file[:st_var_line + offset] + ['    uint256 _prev_var = 0;\n'] + raw_file[
                                                                                                    st_var_line + offset:]
    return replaced_file

def add_check_logic(c: Node, raw_file:list, offset, already_add=0):
    c_line_start = c.source_mapping['lines'][0]
    c_line_end = c.source_mapping['lines'][-1]
    tab_num = c.source_mapping['starting_column'] - 1
    tabs = ''.join([' ' for _ in range(tab_num)])
    if already_add == 0:
        replaced_file = (raw_file[: c_line_start + offset - 1] + [tabs + 'uint start=_prev_var;\n']
                         + raw_file[c_line_start + offset - 1: c_line_end + offset] +
                         [tabs + 'if(_prev_var != start) revert();\n',
                          tabs + '_prev_var = start + 1;\n'] +
                         raw_file[c_line_end + offset:])
    else:
        replaced_file = (raw_file[: c_line_start + offset - 1] + [tabs + 'start=_prev_var;\n']
                         + raw_file[c_line_start + offset - 1: c_line_end + offset] +
                         [tabs + 'if(_prev_var != start) revert();\n',
                          tabs + '_prev_var = start + 1;\n'] +
                         raw_file[c_line_end + offset:])
    return replaced_file

def post_reentrancy_check_inject(src_path, dest_path):
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
        visit_functions = set()
        for ct in contracts:
            replaced_file = add_pre_var(ct, replaced_file, offset)
            offset += 1
            external_calls = tmp.get(ct, set())
            external_calls = list(external_calls)
            external_calls = sorted(external_calls, key=lambda x: x.source_mapping['lines'][0])
            for c in external_calls:
                if c.function in visit_functions:
                    replaced_file = add_check_logic(c, replaced_file, offset, 1)
                else:
                    visit_functions.add(c.function)
                    replaced_file = add_check_logic(c, replaced_file, offset, 0)
                offset += 3
    write_file(dest_path, replaced_file)
    return 0

if __name__ == '__main__':
    src_path = './reentrancy_vul/0xbaf51e761510c1a11bf48dd87c0307ac8a8c8a4f.sol'
    dest_path = 'test.sol'
    post_reentrancy_check_inject(src_path, dest_path)