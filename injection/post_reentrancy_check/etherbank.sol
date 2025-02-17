/*
 * @source: https://github.com/seresistvanandras/EthBench/blob/master/Benchmark/Simple/reentrant.sol
 * @author: -
 * @vulnerable_at_lines: 21
 */

pragma solidity ^0.4.0;
contract EtherBank{
    uint256 _prev_var = 0;
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
      uint start=_prev_var;
		if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }
      if(_prev_var != start) revert();
      _prev_var = start + 1;
		userBalances[msg.sender] = 0;
	}    
}