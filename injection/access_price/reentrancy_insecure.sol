/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 17
 */

pragma solidity ^0.5.0;
contract INJECTED_Ownable{
    address private _owner;
    constructor () public {
        _owner = msg.sender;
    }
    modifier injected_onlyOwner() {
        require(_owner == msg.sender, "Ownable: caller is not the owner");
        _;
    }
}

contract Reentrancy_insecure  is INJECTED_Ownable {

    // INSECURE
    mapping (address => uint) private userBalances;

    function withdrawBalance() public  injected_onlyOwner {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
        require(success);
        userBalances[msg.sender] = 0;
    }
}
