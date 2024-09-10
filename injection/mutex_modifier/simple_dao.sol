/*
 * @source: http://blockchain.unica.it/projects/ethereum-survey/attacks.html#simpledao
 * @author: -
 * @vulnerable_at_lines: 19
 */

pragma solidity ^0.4.2;

contract SimpleDAO {
    bool _injected_mutex_var = false;
  mapping (address => uint) public credit;

   modifier injected_swap(){
       _injected_mutex_var = true;
       _;
       _injected_mutex_var = false;
   }

  function donate(address to) payable {
    credit[to] += msg.value;
  }

  function withdraw(uint amount)  injected_swap {
    if (credit[msg.sender]>= amount) {
      // <yes> <report> REENTRANCY
      require(_injected_mutex_var);
      bool res = msg.sender.call.value(amount)();
      credit[msg.sender]-=amount;
    }
  }

  function queryCredit(address to) returns (uint){
    return credit[to];
  }
}
