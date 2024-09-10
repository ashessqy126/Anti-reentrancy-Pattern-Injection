/*
 * @source: https://github.com/SmartContractSecurity/SWC-registry/blob/master/test_cases/reentracy/modifier_reentrancy.sol
 * @author: - 
 * @vulnerable_at_lines: 15
 */

pragma solidity ^0.4.24;
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

contract ModifierEntrancy {
    address _authorized = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
  mapping (address => uint) public tokenBalance;
  string constant name = "Nu Token";

  //If a contract has a zero balance and supports the token give them some token
  // <yes> <report> REENTRANCY
  function airDrop(bytes32 data, bytes memory signature) hasNoBalance supportsToken  public{
      require(ECDSA.recover(data, signature) == _authorized);
    tokenBalance[msg.sender] += 20;
  }

  //Checks that the contract responds the way we want
  modifier supportsToken() {
    require(keccak256(abi.encodePacked("Nu Token")) == Bank(msg.sender).supportsToken());
    _;
  }
  //Checks that the caller has a zero balance
  modifier hasNoBalance {
      require(tokenBalance[msg.sender] == 0);
      _;
  }
}

contract Bank{
    function supportsToken() external pure returns(bytes32){
        return(keccak256(abi.encodePacked("Nu Token")));
    }
}

//contract attack{ //An example of a contract that breaks the contract above.
//    bool hasBeenCalled;
//    function supportsToken() external returns(bytes32){
//        if(!hasBeenCalled){
//             hasBeenCalled = true;
//             ModifierEntrancy(msg.sender).airDrop();
//         }
//         return(keccak256(abi.encodePacked("Nu Token")));
//     }
//     function call(address token) public{
//         ModifierEntrancy(token).airDrop();
//     }
// }
