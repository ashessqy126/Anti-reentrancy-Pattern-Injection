/*
 * @source: https://github.com/ConsenSys/evm-analyzer-benchmark-suite
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 18
 */

pragma solidity ^0.4.19;

contract ReentrancyDAO {
    bool _injected_mutex_var = false;
    mapping (address => uint) credit;
    uint balance;

     modifier injected_swap(){
         _injected_mutex_var = true;
         _;
         _injected_mutex_var = false;
     }

    function withdrawAll() public  injected_swap {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            // <yes> <report> REENTRANCY
            require(_injected_mutex_var);
            bool callResult = msg.sender.call.value(oCredit)();
            require (callResult);
            credit[msg.sender] = 0;
        }
    }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        balance += msg.value;
    }
}
