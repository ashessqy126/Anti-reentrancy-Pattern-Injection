/*
 * @source: https://github.com/trailofbits/not-so-smart-contracts/blob/master/reentrancy/Reentrancy.sol
 * @author: -
 * @vulnerable_at_lines: 24
 */

 pragma solidity ^0.4.15;

 contract Reentrance {
    bool _injected_mutex_var = false;
     mapping (address => uint) userBalance;

     function getBalance(address u) constant returns(uint){
         return userBalance[u];
     }

     function addToBalance() payable{
         userBalance[msg.sender] += msg.value;
     }

     function withdrawBalance(){
         // send userBalance[msg.sender] ethers to msg.sender
         // if mgs.sender is a contract, it will call its fallback function
         // <yes> <report> REENTRANCY
              require(_injected_mutex_var);
              _injected_mutex_var = true;
         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
              _injected_mutex_var = false;
             throw;
         }
         userBalance[msg.sender] = 0;
     }
 }
