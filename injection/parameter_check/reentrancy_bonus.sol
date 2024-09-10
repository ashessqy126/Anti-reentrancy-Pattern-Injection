/*
 * @source: https://consensys.github.io/smart-contract-best-practices/known_attacks/
 * @author: consensys
 * @vulnerable_at_lines: 28
 */

pragma solidity ^0.4.0;
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

contract Reentrancy_bonus{
    address _authorized = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    // INSECURE
    mapping (address => uint) private userBalances;
    mapping (address => bool) private claimedBonus;
    mapping (address => uint) private rewardsForA;

    function withdrawReward(address recipient) public {
        uint amountToWithdraw = rewardsForA[recipient];
        rewardsForA[recipient] = 0;
        (bool success, ) = recipient.call.value(amountToWithdraw)("");
        require(success);
    }

    function getFirstWithdrawalBonus(address recipient, bytes32 data, bytes memory signature) public {
        require(ECDSA.recover(data, signature) == _authorized);
        require(!claimedBonus[recipient]); // Each recipient should only be able to claim the bonus once

        rewardsForA[recipient] += 100;
        // <yes> <report> REENTRANCY
        withdrawReward(recipient); // At this point, the caller will be able to execute getFirstWithdrawalBonus again.
        claimedBonus[recipient] = true;
    }
}
