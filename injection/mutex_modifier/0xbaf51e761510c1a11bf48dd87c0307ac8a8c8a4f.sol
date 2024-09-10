/*
 * @source: etherscan.io 
 * @author: -
 * @vulnerable_at_lines: 41
 */

pragma solidity ^0.4.19;

contract ETH_VAULT
{
    bool _injected_mutex_var = false;
    mapping (address => uint) public balances;
    
    uint public MinDeposit = 1 ether;
    
    Log TransferLog;

     modifier injected_swap(){
         _injected_mutex_var = true;
         _;
         _injected_mutex_var = false;
     }
    
    function ETH_VAULT(address _log)
    public 
    {
        TransferLog = Log(_log);
    }
    
    function Deposit()
    public
    payable
    {
        if(msg.value > MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
        }
    }
    
    function CashOut(uint _am)
    public
    payable
     injected_swap {
        if(_am<=balances[msg.sender])
        {
            // <yes> <report> REENTRANCY
               require(_injected_mutex_var);
            if(msg.sender.call.value(_am)
            ())
            {
                balances[msg.sender]-=_am;
                TransferLog.AddMessage(msg.sender,_am,"CashOut");
            }
        }
    }
    
    function() public payable{}    
    
}

contract Log 
{
   
    struct Message
    {
        address Sender;
        string  Data;
        uint Val;
        uint  Time;
    }
    
    Message[] public History;
    
    Message LastMsg;
    
    function AddMessage(address _adr,uint _val,string _data)
    public
    {
        LastMsg.Sender = _adr;
        LastMsg.Time = now;
        LastMsg.Val = _val;
        LastMsg.Data = _data;
        History.push(LastMsg);
    }
}