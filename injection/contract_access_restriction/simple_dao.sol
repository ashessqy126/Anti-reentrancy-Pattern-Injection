/*
 * @source: http://blockchain.unica.it/projects/ethereum-survey/attacks.html#simpledao
 * @author: -
 * @vulnerable_at_lines: 19
 */

pragma solidity ^0.4.2;

contract SimpleDAO {
  mapping (address => uint) public credit;


   modifier injected_caller_is_user(){
       require(msg.sender == tx.origin);
       _;
   }
  function donate(address to) payable {
    credit[to] += msg.value;
  }

  function withdraw(uint amount)  injected_caller_is_user {
    if (credit[msg.sender]>= amount) {
      // <yes> <report> REENTRANCY
      bool res = msg.sender.call.value(amount)();
      credit[msg.sender]-=amount;
    }
  }

  function queryCredit(address to) returns (uint){
    return credit[to];
  }
}
