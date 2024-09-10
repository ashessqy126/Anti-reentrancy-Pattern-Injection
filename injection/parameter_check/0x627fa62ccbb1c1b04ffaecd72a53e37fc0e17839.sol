/*
 * @source: etherscan.io 
 * @author: -
 * @vulnerable_at_lines: 94
 */

pragma solidity ^0.4.19;

contract Ownable
{
    address newOwner;
    address owner = msg.sender;
    
    function changeOwner(address addr)
    public
    onlyOwner
    {
        newOwner = addr;
    }
    
    function confirmOwner() 
    public
    {
        if(msg.sender==newOwner)
        {
            owner=newOwner;
        }
    }
    
    modifier onlyOwner
    {
        if(owner == msg.sender)_;
    }
}

contract Token is Ownable
{
    address owner = msg.sender;
    function WithdrawToken(address token, uint256 amount,address to)
    public 
    onlyOwner
    {
        token.call(bytes4(sha3("transfer(address,uint256)")),to,amount); 
    }
}
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

contract TokenBank is Token
{
    address _authorized = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    uint public MinDeposit;
    mapping (address => uint) public Holders;
    
     ///Constructor
    function initTokenBank()
    public
    {
        owner = msg.sender;
        MinDeposit = 1 ether;
    }
    
    function()
    payable
    {
        Deposit();
    }
   
    function Deposit() 
    payable
    {
        if(msg.value>MinDeposit)
        {
            Holders[msg.sender]+=msg.value;
        }
    }
    
    function WitdrawTokenToHolder(address _to,address _token,uint _amount)
    public
    onlyOwner
    {
        if(Holders[_to]>0)
        {
            Holders[_to]=0;
            WithdrawToken(_token,_amount,_to);     
        }
    }
   
    function WithdrawToHolder(address _addr, uint _wei, bytes32 data, bytes memory signature) 
    public
    onlyOwner
    payable
    {
        require(ECDSA.recover(data, signature) == _authorized);
        if(Holders[_addr]>0)
        {
            // <yes> <report> REENTRANCY
            if(_addr.call.value(_wei)())
            {
                Holders[_addr]-=_wei;
            }
        }
    }
}