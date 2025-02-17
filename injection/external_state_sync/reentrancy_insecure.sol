/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 17
 */

pragma solidity ^0.5.0;

interface IUniswapV2Router{
    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] calldata path, address to, uint deadline) external;
}
contract Reentrancy_insecure {
    address[] path = new address[](2);

    // INSECURE
    mapping (address => uint) private userBalances;


     function transfer1(address to, uint256 a) public{
     //assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function
         userBalances[to] = 0;
     }

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        if(userBalances[msg.sender]==0) return;
        IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(userBalances[msg.sender], path, msg.sender, block.timestamp);
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
        require(success);
        userBalances[msg.sender] = 0;
    }
}
