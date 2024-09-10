/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 24
 */

pragma solidity ^0.4.0;

contract Reentrancy_cross_function {
    bool _injected_mutex_var = false;

    // INSECURE
    mapping (address => uint) private userBalances;

     modifier injected_swap(){
         _injected_mutex_var = true;
         _;
         _injected_mutex_var = false;
     }

    function transfer(address to, uint amount) {
        if (userBalances[msg.sender] >= amount) {
            userBalances[to] += amount;
            userBalances[msg.sender] -= amount;
        }
    }

    function withdrawBalance() public  injected_swap {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        require(_injected_mutex_var);
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call transfer()
        require(success);
        userBalances[msg.sender] = 0;
    }
}
