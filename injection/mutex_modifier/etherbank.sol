/*
 * @source: https://github.com/seresistvanandras/EthBench/blob/master/Benchmark/Simple/reentrant.sol
 * @author: -
 * @vulnerable_at_lines: 21
 */

pragma solidity ^0.4.0;
contract EtherBank{
    bool _injected_mutex_var = false;

     modifier injected_swap(){
         _injected_mutex_var = true;
         _;
         _injected_mutex_var = false;
     }
    mapping (address => uint) userBalances;
    function getBalance(address user) constant returns(uint) {  
		return userBalances[user];
	}

	function addToBalance() {  
		userBalances[msg.sender] += msg.value;
	}

	function withdrawBalance()  injected_swap {  
		uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
      require(_injected_mutex_var);
		if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }
		userBalances[msg.sender] = 0;
	}    
}