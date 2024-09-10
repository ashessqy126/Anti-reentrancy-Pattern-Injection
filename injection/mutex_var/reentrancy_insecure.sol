/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 17
 */

pragma solidity ^0.5.0;

contract Reentrancy_insecure {
    bool _injected_mutex_var = false;

    // INSECURE
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
         require(_injected_mutex_var);
         _injected_mutex_var = true;
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
         _injected_mutex_var = false;
        require(success);
        userBalances[msg.sender] = 0;
    }
}
