// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {CreditToken} from "./CreditToken.sol";

contract RebatePool {
    CreditToken public token;
    address public market;
    address public immutable owner = msg.sender;

    mapping(address => uint256) public claimable;

    constructor(CreditToken creditToken) {
        token = creditToken;
    }

    function setMarket(address marketAddress) external {
        require(msg.sender == owner && market == address(0));
        market = marketAddress;
    }

    function accrue(address user, uint256 amount) external {
        require(msg.sender == market);
        claimable[user] += amount;
    }

    function sync(address user, uint256 amount) external {
        require(msg.sender == market);
        claimable[user] = amount;
    }

    function claim(address user) external {
        require(msg.sender == market);

        uint256 amount = claimable[user];
        require(amount > 0);

        claimable[user] = 0;
        token.transfer(user, amount);
    }
}
