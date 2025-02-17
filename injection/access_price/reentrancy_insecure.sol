/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 17
 */

pragma solidity ^0.5.0;

contract Reentrancy_insecure {
    uint256 public SALE_PRICE = 0.002 ether;

    // INSECURE
    mapping (address => uint) private userBalances;

    function withdrawBalance() public  payable {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        require(msg.value >= SALE_PRICE);
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
        require(success);
        userBalances[msg.sender] = 0;
    }
}
