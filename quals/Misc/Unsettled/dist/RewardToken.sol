// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IReceiver {
    function onRewardReceived() external;
}

contract RewardToken {
    mapping(address => uint256) public balanceOf;
    mapping(address => bool) public hook;
    address public immutable owner = msg.sender;

    function setHook(bool enabled) external {
        hook[msg.sender] = enabled;
    }

    function transfer(address to, uint256 amount) external {
        require(balanceOf[msg.sender] >= amount);

        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;

        if (hook[to] && to.code.length > 0) {
            IReceiver(to).onRewardReceived();
        }
    }

    function mint(address to, uint256 amount) external {
        require(msg.sender == owner);
        balanceOf[to] += amount;
    }
}
