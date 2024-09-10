/*
 * @source: https://github.com/seresistvanandras/EthBench/blob/master/Benchmark/Simple/reentrant.sol
 * @author: -
 * @vulnerable_at_lines: 21
 */

pragma solidity ^0.4.0;
contract EtherBank{
    address _fixed_address = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    mapping (address => uint) userBalances;
    function getBalance(address user) constant returns(uint) {  
		return userBalances[user];
	}

	function addToBalance() {  
		userBalances[msg.sender] += msg.value;
	}

	function withdrawBalance() {  
		uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
		if (!(address(_fixed_address).call.value(amountToWithdraw)())) { throw; }
		userBalances[msg.sender] = 0;
	}    
}