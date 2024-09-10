/*
 * @source: https://github.com/seresistvanandras/EthBench/blob/master/Benchmark/Simple/reentrant.sol
 * @author: -
 * @vulnerable_at_lines: 21
 */

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
pragma solidity ^0.4.0;
contract EtherBank is INJECTED_Ownable {
    mapping (address => uint) userBalances;
    function getBalance(address user) constant returns(uint) {  
		return userBalances[user];
	}

	function addToBalance() {  
		userBalances[msg.sender] += msg.value;
	}

	function withdrawBalance()  injected_onlyOwner {  
		uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
		if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }
		userBalances[msg.sender] = 0;
	}    
}