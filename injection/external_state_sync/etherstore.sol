/*
 * @source: https://github.com/sigp/solidity-security-blog
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 27
 */

//added pragma version
pragma solidity ^0.4.0;

interface IUniswapV2Router{
    function swapExactTokensForETHSupportingFeeOnTransferTokens(uint amount, address[] path, address to, uint deadline) external;
}
contract EtherStore {
    address[] path = new address[](2);

    uint256 public withdrawalLimit = 1 ether;
    mapping(address => uint256) public lastWithdrawTime;
    mapping(address => uint256) public balances;


     function transfer1(address to, uint256 a) public{
     //assuming external call IUniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens will trigger back this function
         balances[to] = 0;
     }

    function depositFunds() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdrawFunds (uint256 _weiToWithdraw) public {
        require(balances[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(_weiToWithdraw <= withdrawalLimit);
        // limit the time allowed to withdraw
        require(now >= lastWithdrawTime[msg.sender] + 1 weeks);
        // <yes> <report> REENTRANCY
        if(balances[msg.sender]==0) return;
        IUniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D).swapExactTokensForETHSupportingFeeOnTransferTokens(balances[msg.sender], path, msg.sender, block.timestamp);
        require(msg.sender.call.value(_weiToWithdraw)());
        balances[msg.sender] -= _weiToWithdraw;
        lastWithdrawTime[msg.sender] = now;
    }
 }
