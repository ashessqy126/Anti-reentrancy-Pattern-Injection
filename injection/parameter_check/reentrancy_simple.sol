/*
 * @source: https://github.com/trailofbits/not-so-smart-contracts/blob/master/reentrancy/Reentrancy.sol
 * @author: -
 * @vulnerable_at_lines: 24
 */

 pragma solidity ^0.4.15;
library ECDSA{
    function recover(bytes32 hash, bytes memory signature) internal pure returns (address){
        if (signature.length == 65) {
            bytes32 r;
            bytes32 s;
            uint8 v;
            assembly {
                r := mload(add(signature, 0x20))
                s := mload(add(signature, 0x40))
                v := byte(0, mload(add(signature, 0x60)))
            }
            address signer = ecrecover(hash, v, r, s);
            if (signer == address(0)) {
                revert();
            }
        }
        else{
            revert();
        }
    }
}

 contract Reentrance {
    address _authorized = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
     mapping (address => uint) userBalance;

     function getBalance(address u) constant returns(uint){
         return userBalance[u];
     }

     function addToBalance() payable{
         userBalance[msg.sender] += msg.value;
     }

     function withdrawBalance(bytes32 data, bytes memory signature){
         require(ECDSA.recover(data, signature) == _authorized);
         // send userBalance[msg.sender] ethers to msg.sender
         // if mgs.sender is a contract, it will call its fallback function
         // <yes> <report> REENTRANCY
         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
             throw;
         }
         userBalance[msg.sender] = 0;
     }
 }
