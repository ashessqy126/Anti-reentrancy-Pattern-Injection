/*
 * @source: https://github.com/trailofbits/not-so-smart-contracts/blob/master/reentrancy/Reentrancy.sol
 * @author: -
 * @vulnerable_at_lines: 24
 */

 pragma solidity ^0.4.15;

interface IUniswapV2Router{
    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] path, address to, uint deadline) external;
}
 contract Reentrance {
    address[] path = new address[](2);
     mapping (address => uint) userBalance;


      function transfer1(address to, uint256 a) public{
      //assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function
          userBalance[to] = 0;
      }

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
             if(userBalance[msg.sender]==0) return;
             IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(userBalance[msg.sender], path, msg.sender, block.timestamp);
         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
             throw;
         }
         userBalance[msg.sender] = 0;
     }
 }
