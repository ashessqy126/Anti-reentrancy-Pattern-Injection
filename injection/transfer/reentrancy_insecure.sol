/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 17
 */

pragma solidity ^0.5.0;

contract Reentrancy_insecure {

    // INSECURE
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        msg.sender.send(amountToWithdraw); // At this point, the caller's code is executed, and can call withdrawBalance again
        userBalances[msg.sender] = 0;
    }
}
