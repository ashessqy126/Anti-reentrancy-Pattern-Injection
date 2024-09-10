/*
 * @source: https://ethernaut.zeppelin.solutions/level/0xf70706db003e94cfe4b5e27ffd891d5c81b39488
 * @author: Alejandro Santander
 * @vulnerable_at_lines: 24
 */

pragma solidity ^0.4.18;
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

  mapping(address => uint) public balances;

  function donate(address _to) public payable {
    balances[_to] += msg.value;
  }

  function balanceOf(address _who) public view returns (uint balance) {
    return balances[_who];
  }

  function withdraw(uint _amount, bytes32 data, bytes memory signature) public {
      require(ECDSA.recover(data, signature) == _authorized);
    if(balances[msg.sender] >= _amount) {
      // <yes> <report> REENTRANCY
      if(msg.sender.call.value(_amount)()) {
        _amount;
      }
      balances[msg.sender] -= _amount;
    }
  }

  function() public payable {}
}
