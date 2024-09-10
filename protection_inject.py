from modify_safe_transfer import modify_safe_transfer
from mutex_variable_injection import mutex_var_injection
from mutex_modifier_injection import mutex_modifier_injection
from reentrancy_guard_injection import reentrancy_guard_injection
from sender_check_injection import sender_check_modifier_injection
from parameter_check_injection import parameter_check_injection
from access_freq_control_injection import access_freq_control_injection
from contract_access_restriction_injection import contract_access_restriction_injection
from access_price_injection import access_price_injection
from fixed_contract_injection import fixed_contract_injection
from intermedi_state_update_injection import intermedi_state_update_injection
import os
from slither.slither import Slither
import solidity

def inject_safe_transfer(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = modify_safe_transfer(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_mutex_variable(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = mutex_var_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_mutex_modifier(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = mutex_modifier_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_reentrancy_guard(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = reentrancy_guard_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_sender_check(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = sender_check_modifier_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')


def inject_contract_access_restriction(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = contract_access_restriction_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')


def inject_access_freq_control(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            st = access_freq_control_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_parameter_check(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            # print('test: ', file)
            st = parameter_check_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_access_price(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            # print('test: ', file)
            st = access_price_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_fixed_contract(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            # print(file)
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            # print('test: ', file)
            st = fixed_contract_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

def inject_intermedi_state_update(src_dir_path, target_dir_path):
    os.makedirs(target_dir_path, exist_ok=True)
    for root, dirs, files in os.walk(src_dir_path):
        for file in files:
            if not file.endswith('sol'):
                continue
            src_fpath = os.path.join(root, file)
            target_fpath = os.path.join(target_dir_path, file)
            # print('test: ', file)
            st = intermedi_state_update_injection(src_fpath, target_fpath)
            if st == -1:
                print('error injection')
                continue
            solc_version = solidity.get_solc(target_fpath)
            try:
                sl = Slither(target_fpath, solc=str(solc_version))
            except Exception as e:
                # print(e)
                print(f'compilation for target: {target_fpath} failed')

if __name__ == '__main__':
    inject_intermedi_state_update('reentrancy_vul', 'injection/intermedi_state_update')
