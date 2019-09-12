pragma solidity ^0.4.24;

contract TimedPiggyBank {
    //owner of piggybank
    address public owner;
    //time that funds can be withdrawn
    uint public endTime;
    
    constructor(uint duration) public {
        //store message sender as piggybank owner
        owner = msg.sender;
        //set endTime
        endTime = now + duration;
    }
    
    //payable function that can be used to deposit funds
    //leaving this blank will allow users to send funds without running any code
    function deposit() public payable {}
    
    function withdraw() public {
        //make sure the message sender is the owner
        require(msg.sender == owner);
        //make sure that the current time is after endTime
        require(now > endTime);
        //send funds to the owner and destroy the contract
        selfdestruct(owner);
    }
    
    function balance() public view returns(uint){
       return address(this).balance;
    }
}
