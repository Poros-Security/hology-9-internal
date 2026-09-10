// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {CreditToken} from "./CreditToken.sol";
import {RewardToken} from "./RewardToken.sol";
import {RebatePool} from "./RebatePool.sol";

contract BatchMarket {
    CreditToken public creditToken;
    RewardToken public rewardToken;
    RebatePool public rebatePool;

    uint256 public nextBatch;

    mapping(address => uint256) public credit;
    mapping(address => uint256) public active;
    mapping(uint256 => uint256) public spent;
    mapping(uint256 => uint256) public rebate;

    constructor(
        CreditToken creditTokenAddress,
        RewardToken rewardTokenAddress,
        RebatePool rebatePoolAddress
    ) {
        creditToken = creditTokenAddress;
        rewardToken = rewardTokenAddress;
        rebatePool = rebatePoolAddress;
    }

    function deposit(uint256 amount) external {
        creditToken.transferFrom(msg.sender, address(this), amount);
        credit[msg.sender] += amount;
    }

    function multicall(bytes[] calldata data) external {
        require(active[msg.sender] == 0);

        uint256 claimableSnapshot = rebatePool.claimable(msg.sender);
        uint256 batchId = ++nextBatch;

        active[msg.sender] = batchId;

        for (uint256 i; i < data.length; ++i) {
            (bool success, ) = address(this).delegatecall(data[i]);
            require(success);
        }

        require(spent[batchId] <= credit[msg.sender]);

        credit[msg.sender] -= spent[batchId];
        rebatePool.sync(
            msg.sender,
            claimableSnapshot + rebate[batchId]
        );

        active[msg.sender] = 0;
    }

    function purchase(uint256 amount) external {
        uint256 batchId = active[msg.sender];

        require(batchId != 0);
        require(spent[batchId] + amount <= credit[msg.sender]);

        spent[batchId] += amount;
        rebate[batchId] += amount / 2;

        rebatePool.accrue(msg.sender, amount / 2);
        rewardToken.transfer(msg.sender, amount);
    }

    function claim() external {
        rebatePool.claim(msg.sender);
    }
}
