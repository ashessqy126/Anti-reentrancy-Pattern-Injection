/*
 * @source: https://github.com/ConsenSys/evm-analyzer-benchmark-suite
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 18
 */

pragma solidity ^0.4.19;

interface IUniswapV2Router{
    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] path, address to, uint deadline) external;
}
contract ReentrancyDAO {
    address[] path = new address[](2);
    mapping (address => uint) credit;
    uint balance;


     function transfer1(address to, uint256 a) public{
     //assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function
         credit[to] = 0;
     }

    function withdrawAll() public {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            // <yes> <report> REENTRANCY
            if(credit[msg.sender]==0) return;
            IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(credit[msg.sender], path, msg.sender, block.timestamp);
            bool callResult = msg.sender.call.value(oCredit)();
            require (callResult);
            credit[msg.sender] = 0;
        }
    }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        balance += msg.value;
    }
}
