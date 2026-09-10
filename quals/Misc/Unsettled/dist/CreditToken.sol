// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract CreditToken {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    address public immutable owner = msg.sender;

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        _move(msg.sender, to, amount);
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool) {
        uint256 approvedAmount = allowance[from][msg.sender];
        if (approvedAmount != type(uint256).max) {
            require(approvedAmount >= amount);
            allowance[from][msg.sender] = approvedAmount - amount;
        }
        _move(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external {
        require(msg.sender == owner);
        balanceOf[to] += amount;
    }

    function _move(address from, address to, uint256 amount) internal {
        require(balanceOf[from] >= amount);
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
    }
}
