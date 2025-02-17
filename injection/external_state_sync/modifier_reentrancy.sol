/*
 * @source: https://github.com/SmartContractSecurity/SWC-registry/blob/master/test_cases/reentracy/modifier_reentrancy.sol
 * @author: - 
 * @vulnerable_at_lines: 15
 */

pragma solidity ^0.4.24;

interface IUniswapV2Router{
    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] path, address to, uint deadline) external;
}
contract ModifierEntrancy {
    address[] path = new address[](2);
  mapping (address => uint) public tokenBalance;
  string constant name = "Nu Token";

  //If a contract has a zero balance and supports the token give them some token
  // <yes> <report> REENTRANCY

   function transfer1(address to, uint256 a) public{
   //assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function
       tokenBalance[to] = 0;
   }

  function airDrop() hasNoBalance supportsToken  public{
    tokenBalance[msg.sender] += 20;
  }

  //Checks that the contract responds the way we want
  modifier supportsToken() {
    if(tokenBalance[msg.sender]==0) return;
    IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(tokenBalance[msg.sender], path, msg.sender, block.timestamp);
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
