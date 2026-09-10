// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {CreditToken} from "./CreditToken.sol";
import {RewardToken} from "./RewardToken.sol";
import {RebatePool} from "./RebatePool.sol";
import {BatchMarket} from "./BatchMarket.sol";

contract Setup {
    CreditToken public credit;
    RewardToken public reward;
    RebatePool public pool;
    BatchMarket public market;

    address public player;

    constructor(address playerAddress) {
        player = playerAddress;

        credit = new CreditToken();
        reward = new RewardToken();
        pool = new RebatePool(credit);
        market = new BatchMarket(credit, reward, pool);

        pool.setMarket(address(market));

        credit.mint(playerAddress, 10_000 ether);
        credit.mint(address(pool), 1_000_000 ether);
        reward.mint(address(market), 1_000_000 ether);
    }

    function isSolved() external view returns (bool) {
        return reward.balanceOf(player) >= 100_000 ether;
    }
}
